# AI Module - Models
from django.db import models
from django.conf import settings
from core.models import Organization


class Conversation(models.Model):
    """
    Représente une conversation avec l'assistant IA
    """
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name='ai_conversations'
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='ai_conversations',
        null=True,
        blank=True
    )
    employee = models.ForeignKey(
        'hr.Employee',
        on_delete=models.CASCADE,
        related_name='ai_conversations',
        null=True,
        blank=True
    )
    title = models.CharField(max_length=255, default="Nouvelle conversation")
    is_agent_mode = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']
        verbose_name = "Conversation IA"
        verbose_name_plural = "Conversations IA"

    def __str__(self):
        return f"{self.title} - {self.organization.name}"


class Message(models.Model):
    """
    Un message dans une conversation
    """
    ROLE_CHOICES = [
        ('user', 'Utilisateur'),
        ('assistant', 'Assistant'),
        ('system', 'Système'),
    ]
    
    FEEDBACK_CHOICES = [
        ('like', 'Utile'),
        ('dislike', 'Pas utile'),
    ]

    conversation = models.ForeignKey(
        Conversation,
        on_delete=models.CASCADE,
        related_name='messages'
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    content = models.TextField()
    feedback = models.CharField(
        max_length=10,
        choices=FEEDBACK_CHOICES,
        null=True,
        blank=True
    )
    # Métadonnées pour le mode agent
    tool_calls = models.JSONField(null=True, blank=True)  # Actions exécutées
    tool_results = models.JSONField(null=True, blank=True)  # Résultats des actions
    tokens_used = models.IntegerField(default=0)
    response_time_ms = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']
        verbose_name = "Message IA"
        verbose_name_plural = "Messages IA"

    def __str__(self):
        return f"{self.role}: {self.content[:50]}..."


class AIToolExecution(models.Model):
    """
    Log des exécutions d'outils par l'agent IA
    """
    STATUS_CHOICES = [
        ('pending', 'En attente'),
        ('running', 'En cours'),
        ('success', 'Succès'),
        ('error', 'Erreur'),
    ]

    message = models.ForeignKey(
        Message,
        on_delete=models.CASCADE,
        related_name='tool_executions'
    )
    tool_name = models.CharField(max_length=100)
    tool_input = models.JSONField()
    tool_output = models.JSONField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    error_message = models.TextField(null=True, blank=True)
    execution_time_ms = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Exécution d'outil IA"
        verbose_name_plural = "Exécutions d'outils IA"

    def __str__(self):
        return f"{self.tool_name} - {self.status}"
