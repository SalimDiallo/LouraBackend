# AI Module - Serializers
from rest_framework import serializers
from .models import Conversation, Message, AIToolExecution


class MessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Message
        fields = [
            'id', 'role', 'content', 'feedback',
            'tool_calls', 'tool_results',
            'tokens_used', 'response_time_ms', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class ConversationSerializer(serializers.ModelSerializer):
    messages = MessageSerializer(many=True, read_only=True)
    message_count = serializers.SerializerMethodField()

    class Meta:
        model = Conversation
        fields = [
            'id', 'title', 'is_agent_mode', 'is_active',
            'messages', 'message_count',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_message_count(self, obj):
        return obj.messages.count()


class ConversationListSerializer(serializers.ModelSerializer):
    """Serializer léger pour la liste des conversations"""
    last_message = serializers.SerializerMethodField()

    class Meta:
        model = Conversation
        fields = ['id', 'title', 'is_agent_mode', 'last_message', 'updated_at']

    def get_last_message(self, obj):
        last = obj.messages.last()
        if last:
            return {
                'content': last.content[:100],
                'role': last.role,
                'created_at': last.created_at
            }
        return None


class ChatRequestSerializer(serializers.Serializer):
    """Serializer pour les requêtes de chat"""
    message = serializers.CharField(max_length=8000)
    conversation_id = serializers.UUIDField(required=False)
    agent_mode = serializers.BooleanField(default=True, required=False)  # Kept for compat, always True
    model = serializers.CharField(max_length=100, required=False)


class FeedbackSerializer(serializers.Serializer):
    """Serializer pour le feedback sur les messages"""
    feedback = serializers.ChoiceField(choices=['like', 'dislike', None])


class AIToolExecutionSerializer(serializers.ModelSerializer):
    class Meta:
        model = AIToolExecution
        fields = [
            'id', 'tool_name', 'tool_input', 'tool_output',
            'status', 'error_message', 'execution_time_ms', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']
