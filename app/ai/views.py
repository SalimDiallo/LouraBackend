# AI Module - Views
import json
import logging

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.http import StreamingHttpResponse

from core.models import Organization
from .models import Conversation, Message, AIToolExecution
from .serializers import (
    ConversationSerializer,
    ConversationListSerializer,
    MessageSerializer,
    ChatRequestSerializer,
    FeedbackSerializer,
)
from .agent import LouraAIAgent
from .config import ai_config

logger = logging.getLogger(__name__)


class ConversationViewSet(viewsets.ModelViewSet):
    """
    ViewSet pour gérer les conversations IA.
    Filtre les conversations par organisation ET par utilisateur courant.
    """
    permission_classes = [IsAuthenticated]
    serializer_class = ConversationSerializer

    def get_queryset(self):
        org_subdomain = self.request.headers.get('X-Organization-Subdomain')
        user = self.request.user

        if org_subdomain:
            return Conversation.objects.filter(
                organization__subdomain=org_subdomain,
                user=user,
                is_active=True
            )
        return Conversation.objects.none()

    def get_serializer_class(self):
        if self.action == 'list':
            return ConversationListSerializer
        return ConversationSerializer

    def perform_create(self, serializer):
        org_subdomain = self.request.headers.get('X-Organization-Subdomain')
        organization = get_object_or_404(Organization, subdomain=org_subdomain)
        user = self.request.user if hasattr(self.request.user, 'email') else None
        employee = getattr(self.request.user, 'employee', None) if hasattr(self.request, 'user') else None
        serializer.save(organization=organization, user=user, employee=employee)

    @action(detail=True, methods=['delete'])
    def clear(self, request, pk=None):
        """Efface tous les messages d'une conversation"""
        conversation = self.get_object()
        conversation.messages.all().delete()
        Message.objects.create(
            conversation=conversation,
            role='assistant',
            content="Conversation effacée. Comment puis-je vous aider ?",
        )
        return Response({'status': 'cleared'})

    @action(detail=True, methods=['post'])
    def feedback(self, request, pk=None):
        """Ajoute un feedback à un message"""
        message_id = request.data.get('message_id')
        serializer = FeedbackSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        message = get_object_or_404(Message, id=message_id, conversation_id=pk)
        message.feedback = serializer.validated_data['feedback']
        message.save()
        return Response({'status': 'feedback saved'})


class ChatView(APIView):
    """
    Endpoint principal pour le chat IA (non-streaming).
    Filtre par utilisateur courant et organisation.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ChatRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data
        message_content = data['message']
        conversation_id = data.get('conversation_id')
        model = data.get('model')

        # Récupérer l'organisation
        org_subdomain = request.headers.get('X-Organization-Subdomain')
        if not org_subdomain:
            return Response(
                {'error': 'X-Organization-Subdomain header required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        organization = get_object_or_404(Organization, subdomain=org_subdomain)
        user = request.user

        # Récupérer ou créer la conversation (filtré par user)
        if conversation_id:
            conversation = get_object_or_404(
                Conversation, id=conversation_id, organization=organization, user=user
            )
        else:
            employee = getattr(user, 'employee', None)
            conversation = Conversation.objects.create(
                organization=organization,
                user=user,
                employee=employee,
                title=message_content[:50] + ("..." if len(message_content) > 50 else ""),
                is_agent_mode=True,
            )

        # Sauvegarder le message utilisateur
        Message.objects.create(
            conversation=conversation,
            role='user',
            content=message_content,
        )

        # Construire l'historique
        history = [
            {'role': msg.role, 'content': msg.content}
            for msg in conversation.messages.all().order_by('created_at')
        ]

        # Appeler l'agent IA avec le contexte utilisateur
        try:
            agent = LouraAIAgent(organization=organization, user=user, model=model)
            result = agent.chat(
                message=message_content,
                conversation_history=history[:-1],
            )
        except ValueError as e:
            return Response(
                {'error': str(e), 'success': False},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        # Sauvegarder la réponse
        assistant_message = Message.objects.create(
            conversation=conversation,
            role='assistant',
            content=result['content'],
            tool_calls=result.get('tool_calls'),
            tool_results=result.get('tool_results'),
            response_time_ms=result.get('response_time_ms', 0),
        )

        # Sauvegarder les exécutions d'outils
        for i, tool_call in enumerate(result.get('tool_calls', [])):
            tool_result = result.get('tool_results', [])[i] if i < len(result.get('tool_results', [])) else {}
            AIToolExecution.objects.create(
                message=assistant_message,
                tool_name=tool_call.get('tool', ''),
                tool_input=tool_call.get('params', {}),
                tool_output=tool_result.get('data'),
                status='success' if tool_result.get('success') else 'error',
                error_message=tool_result.get('error'),
            )

        return Response({
            'success': result.get('success', True),
            'content': result['content'],
            'conversation_id': str(conversation.id),
            'message_id': str(assistant_message.id),
            'tool_calls': result.get('tool_calls', []),
            'tool_results': result.get('tool_results', []),
            'response_time_ms': result.get('response_time_ms', 0),
            'model': result.get('model', 'unknown'),
        })


class ChatStreamView(APIView):
    """
    Endpoint pour le chat IA avec streaming (Server-Sent Events).
    Filtre par utilisateur courant et organisation.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ChatRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data
        message_content = data['message']
        conversation_id = data.get('conversation_id')
        model = data.get('model')

        # Récupérer l'organisation
        org_subdomain = request.headers.get('X-Organization-Subdomain')
        if not org_subdomain:
            return Response(
                {'error': 'X-Organization-Subdomain header required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        organization = get_object_or_404(Organization, subdomain=org_subdomain)
        user = request.user

        # Récupérer ou créer la conversation (filtré par user)
        if conversation_id:
            conversation = get_object_or_404(
                Conversation, id=conversation_id, organization=organization, user=user
            )
        else:
            employee = getattr(user, 'employee', None)
            conversation = Conversation.objects.create(
                organization=organization,
                user=user,
                employee=employee,
                title=message_content[:50] + ("..." if len(message_content) > 50 else ""),
                is_agent_mode=True,
            )

        # Sauvegarder le message utilisateur
        Message.objects.create(
            conversation=conversation,
            role='user',
            content=message_content,
        )

        # Construire l'historique
        history = [
            {'role': msg.role, 'content': msg.content}
            for msg in conversation.messages.all().order_by('created_at')
        ]

        def generate():
            try:
                agent = LouraAIAgent(organization=organization, user=user, model=model)
                full_content = ""
                all_tool_calls = []
                all_tool_results = []

                for event in agent.chat_stream(
                    message=message_content,
                    conversation_history=history[:-1],
                ):
                    event_type = event.get("type")

                    if event_type == "token":
                        full_content += event.get("content", "")
                        yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"

                    elif event_type == "tool_executing":
                        yield f"data: {json.dumps(event, ensure_ascii=False, default=str)}\n\n"

                    elif event_type == "confirmation_required":
                        yield f"data: {json.dumps(event, ensure_ascii=False, default=str)}\n\n"

                    elif event_type == "tools":
                        all_tool_calls = event.get("tool_calls", [])
                        all_tool_results = event.get("tool_results", [])
                        yield f"data: {json.dumps(event, ensure_ascii=False, default=str)}\n\n"
                        # Clear the accumulated content since we'll get a new response
                        yield f"data: {json.dumps({'type': 'clear'})}\n\n"
                        full_content = ""

                    elif event_type == "done":
                        # Sauvegarder la réponse
                        assistant_message = Message.objects.create(
                            conversation=conversation,
                            role='assistant',
                            content=full_content,
                            tool_calls=all_tool_calls or None,
                            tool_results=all_tool_results or None,
                        )

                        # Sauvegarder les exécutions d'outils
                        for i, tc in enumerate(all_tool_calls):
                            tr = all_tool_results[i] if i < len(all_tool_results) else {}
                            AIToolExecution.objects.create(
                                message=assistant_message,
                                tool_name=tc.get('tool', ''),
                                tool_input=tc.get('params', {}),
                                tool_output=tr.get('data'),
                                status='success' if tr.get('success') else 'error',
                                error_message=tr.get('error'),
                            )

                        done_data = {
                            'type': 'done',
                            'conversation_id': str(conversation.id),
                            'message_id': str(assistant_message.id),
                        }
                        yield f"data: {json.dumps(done_data)}\n\n"

                    elif event_type == "error":
                        yield f"data: {json.dumps(event)}\n\n"

            except ValueError as e:
                yield f"data: {json.dumps({'type': 'error', 'error': str(e)})}\n\n"
            except Exception as e:
                logger.error(f"Streaming error: {e}", exc_info=True)
                yield f"data: {json.dumps({'type': 'error', 'error': str(e)})}\n\n"

        response = StreamingHttpResponse(
            generate(),
            content_type='text/event-stream'
        )
        response['Cache-Control'] = 'no-cache'
        response['X-Accel-Buffering'] = 'no'
        return response


class AIToolsView(APIView):
    """
    Endpoint pour lister les outils disponibles pour l'agent
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        from .tools import registry

        tools = [
            {
                'name': tool.name,
                'description': tool.description,
                'category': tool.category,
                'is_read_only': tool.is_read_only,
                'params': list(tool.parameters.get('properties', {}).keys()),
            }
            for tool in registry.get_all().values()
        ]

        return Response({
            'tools': tools,
            'total': len(tools),
        })


class AIConfigView(APIView):
    """
    Endpoint pour récupérer la configuration IA
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response({
            'configured': ai_config.is_configured(),
            'model': ai_config.MODEL,
            'provider': 'openai',
            'tools_enabled': ai_config.ENABLE_TOOLS,
        })


class ExecuteToolView(APIView):
    """
    Endpoint pour exécuter un outil confirmé par l'utilisateur (Human-in-the-loop).
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        from .tools import registry

        tool_name = request.data.get('tool_name')
        tool_args = request.data.get('tool_args', {})
        conversation_id = request.data.get('conversation_id')

        if not tool_name:
            return Response(
                {'error': 'tool_name est requis'},
                status=status.HTTP_400_BAD_REQUEST
            )

        org_subdomain = request.headers.get('X-Organization-Subdomain')
        if not org_subdomain:
            return Response(
                {'error': 'X-Organization-Subdomain header required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        organization = get_object_or_404(Organization, subdomain=org_subdomain)

        # Vérifier que l'outil existe
        tool_def = registry.get(tool_name)
        if not tool_def:
            return Response(
                {'error': f"Outil '{tool_name}' introuvable"},
                status=status.HTTP_404_NOT_FOUND
            )

        # Exécuter l'outil
        try:
            if 'organization' in tool_def.parameters.get('properties', {}):
                tool_args['organization'] = organization
            else:
                tool_args['org'] = organization

            result = tool_def.function(**tool_args)

            # Sauvegarder l'exécution si conversation_id fourni
            if conversation_id:
                try:
                    conversation = Conversation.objects.get(
                        id=conversation_id,
                        organization=organization,
                        user=request.user
                    )
                    last_message = conversation.messages.filter(role='assistant').last()
                    if last_message:
                        AIToolExecution.objects.create(
                            message=last_message,
                            tool_name=tool_name,
                            tool_input=tool_args,
                            tool_output=result,
                            status='success' if result.get('success') else 'error',
                            error_message=result.get('error'),
                        )
                except Conversation.DoesNotExist:
                    pass

            return Response({
                'success': True,
                'tool': tool_name,
                'data': result,
            })

        except Exception as e:
            logger.error(f"Tool execution error: {e}", exc_info=True)
            return Response({
                'success': False,
                'tool': tool_name,
                'error': str(e),
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
