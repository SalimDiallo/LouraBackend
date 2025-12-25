# AI Module - Admin
from django.contrib import admin
from .models import Conversation, Message, AIToolExecution


@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = ['title', 'organization', 'user', 'is_agent_mode', 'is_active', 'updated_at']
    list_filter = ['is_agent_mode', 'is_active', 'organization']
    search_fields = ['title', 'user__email']
    ordering = ['-updated_at']


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ['conversation', 'role', 'content_preview', 'feedback', 'created_at']
    list_filter = ['role', 'feedback', 'created_at']
    search_fields = ['content']
    ordering = ['-created_at']
    
    def content_preview(self, obj):
        return obj.content[:50] + "..." if len(obj.content) > 50 else obj.content
    content_preview.short_description = "Contenu"


@admin.register(AIToolExecution)
class AIToolExecutionAdmin(admin.ModelAdmin):
    list_display = ['tool_name', 'status', 'execution_time_ms', 'created_at']
    list_filter = ['tool_name', 'status']
    ordering = ['-created_at']
