# AI Module - Views
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
import uuid

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


class ConversationViewSet(viewsets.ModelViewSet):
    """
    ViewSet pour gérer les conversations IA
    """
    permission_classes = [IsAuthenticated]
    serializer_class = ConversationSerializer
    
    def get_queryset(self):
        # Récupérer l'organisation depuis le header ou le paramètre
        org_subdomain = self.request.headers.get('X-Organization-Subdomain')
        
        if org_subdomain:
            return Conversation.objects.filter(
                organization__subdomain=org_subdomain,
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
        
        # Déterminer l'utilisateur (Admin ou Employee)
        user = self.request.user if hasattr(self.request.user, 'email') else None
        employee = getattr(self.request.user, 'employee', None) if hasattr(self.request, 'user') else None
        
        serializer.save(
            organization=organization,
            user=user,
            employee=employee
        )
    
    @action(detail=True, methods=['delete'])
    def clear(self, request, pk=None):
        """Efface tous les messages d'une conversation"""
        conversation = self.get_object()
        conversation.messages.all().delete()
        
        # Créer un message de bienvenue
        Message.objects.create(
            conversation=conversation,
            role='assistant',
            content="Conversation effacée ! 🧹 Comment puis-je vous aider ?"
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
    Endpoint principal pour le chat IA
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        serializer = ChatRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        data = serializer.validated_data
        message_content = data['message']
        conversation_id = data.get('conversation_id')
        agent_mode = data.get('agent_mode', False)
        model = data.get('model')
        
        # Récupérer l'organisation
        org_subdomain = request.headers.get('X-Organization-Subdomain')
        if not org_subdomain:
            return Response(
                {'error': 'X-Organization-Subdomain header required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        organization = get_object_or_404(Organization, subdomain=org_subdomain)
        
        # Récupérer ou créer la conversation
        if conversation_id:
            conversation = get_object_or_404(
                Conversation,
                id=conversation_id,
                organization=organization
            )
        else:
            # Créer une nouvelle conversation
            user = request.user if hasattr(request.user, 'email') else None
            employee = getattr(request.user, 'employee', None) if hasattr(request, 'user') else None
            
            conversation = Conversation.objects.create(
                organization=organization,
                user=user,
                employee=employee,
                title=message_content[:50] + "..." if len(message_content) > 50 else message_content,
                is_agent_mode=agent_mode
            )
        
        # Sauvegarder le message utilisateur
        user_message = Message.objects.create(
            conversation=conversation,
            role='user',
            content=message_content
        )
        
        # Construire l'historique
        history = [
            {'role': msg.role, 'content': msg.content}
            for msg in conversation.messages.all().order_by('created_at')
        ]
        
        # Appeler l'agent IA
        agent = LouraAIAgent(organization=organization, model=model)
        result = agent.chat(
            message=message_content,
            conversation_history=history[:-1],  # Exclure le message courant
            agent_mode=agent_mode
        )
        
        # Sauvegarder la réponse de l'assistant
        assistant_message = Message.objects.create(
            conversation=conversation,
            role='assistant',
            content=result['content'],
            tool_calls=result.get('tool_calls'),
            tool_results=result.get('tool_results'),
            response_time_ms=result.get('response_time_ms', 0)
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
                execution_time_ms=tool_result.get('execution_time_ms', 0)
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
    Endpoint pour le chat IA avec streaming (Server-Sent Events)
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        import json
        from django.http import StreamingHttpResponse
        
        serializer = ChatRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        data = serializer.validated_data
        message_content = data['message']
        agent_mode = data.get('agent_mode', False)
        model = data.get('model')
        
        # Récupérer l'organisation
        org_subdomain = request.headers.get('X-Organization-Subdomain')
        if not org_subdomain:
            return Response(
                {'error': 'X-Organization-Subdomain header required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        organization = get_object_or_404(Organization, subdomain=org_subdomain)
        
        def generate():
            try:
                import ollama
                
                agent = LouraAIAgent(organization=organization, model=model)
                org_name = organization.name
                
                if agent_mode:
                    system_prompt = agent.AGENT_SYSTEM_PROMPT.format(
                        org_name=org_name,
                        tools_description=agent._get_tools_description()
                    )
                else:
                    system_prompt = agent.SYSTEM_PROMPT.format(org_name=org_name)
                
                messages = [{"role": "system", "content": system_prompt}]
                messages.append({"role": "user", "content": message_content})
                
                # Streaming avec Ollama
                full_content = ""
                for chunk in ollama.chat(
                    model=agent.model,
                    messages=messages,
                    stream=True
                ):
                    if hasattr(chunk, 'message') and hasattr(chunk.message, 'content'):
                        token = chunk.message.content
                        full_content += token
                        yield f"data: {json.dumps({'type': 'token', 'content': token})}\n\n"
                
                # Si mode agent, traiter les actions après le streaming complet
                tool_calls = []
                tool_results = []
                
                if agent_mode and "<action>" in full_content:
                    _, tool_calls, tool_results = agent._process_agent_actions(full_content)
                    
                    if tool_results:
                        # Envoyer les résultats des outils
                        yield f"data: {json.dumps({'type': 'tools', 'tool_calls': tool_calls, 'tool_results': tool_results})}\n\n"
                        
                        # Générer la réponse finale basée sur les données
                        results_data = agent._format_tool_results_for_ai(tool_results)
                        messages.append({"role": "assistant", "content": full_content})
                        messages.append({
                            "role": "user",
                            "content": f"Voici les données RÉELLES. Réponds UNIQUEMENT basé sur celles-ci:\n{results_data}"
                        })
                        
                        yield f"data: {json.dumps({'type': 'clear'})}\n\n"
                        
                        for chunk in ollama.chat(
                            model=agent.model,
                            messages=messages,
                            stream=True
                        ):
                            if hasattr(chunk, 'message') and hasattr(chunk.message, 'content'):
                                token = chunk.message.content
                                yield f"data: {json.dumps({'type': 'token', 'content': token})}\n\n"
                
                yield f"data: {json.dumps({'type': 'done'})}\n\n"
                
            except Exception as e:
                yield f"data: {json.dumps({'type': 'error', 'error': str(e)})}\n\n"
        
        response = StreamingHttpResponse(
            generate(),
            content_type='text/event-stream'
        )
        response['Cache-Control'] = 'no-cache'
        response['X-Accel-Buffering'] = 'no'
        return response


class AIModelsView(APIView):
    """
    Endpoint pour lister les modèles IA disponibles
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        agent = LouraAIAgent()
        models = agent.get_available_models()
        
        return Response({
            'models': models,
            'default': LouraAIAgent.DEFAULT_MODEL,
            'ollama_available': len(models) > 0
        })


class AIToolsView(APIView):
    """
    Endpoint pour lister les outils disponibles pour l'agent
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        agent = LouraAIAgent()
        tools = [
            {
                'name': name,
                'description': tool['description'],
                'params': tool['params']
            }
            for name, tool in agent.tools.items()
        ]
        
        return Response({'tools': tools})

