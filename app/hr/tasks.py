"""
HR Celery Tasks
================
Tâches asynchrones pour le module HR:
- Envoi d'emails d'invitation
"""

import logging
from celery import shared_task
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def send_invitation_email(self, invitation_id):
    """
    Envoie l'email d'invitation à l'employee.
    Retry 3 fois en cas d'échec avec backoff exponentiel.

    Args:
        invitation_id (str): UUID de l'invitation
    """
    from .models import EmployeeInvitation

    try:
        invitation = EmployeeInvitation.objects.get(id=invitation_id)

        # Skip if invitation is not pending
        if invitation.status != EmployeeInvitation.InvitationStatus.PENDING:
            logger.warning(
                f"Skipping email for invitation {invitation_id} - "
                f"status is {invitation.status}"
            )
            return

        # Context for email template
        context = {
            'invitation': invitation,
            'organization_name': invitation.organization.name,
            'inviter_name': invitation.invited_by.get_full_name() if invitation.invited_by else 'Administrator',
            'invitation_url': invitation.get_invitation_url(),
            'expires_at': invitation.expires_at,
            'role_name': invitation.assigned_role.name if invitation.assigned_role else 'Employee',
            'days_until_expiry': (invitation.expires_at - invitation.sent_at).days,
        }

        # Render email templates
        try:
            html_message = render_to_string(
                'emails/employee_invitation.html',
                context
            )
        except Exception as e:
            logger.warning(f"HTML template not found: {e}, using plain text only")
            html_message = None

        text_message = render_to_string(
            'emails/employee_invitation.txt',
            context
        )

        # Send email
        send_mail(
            subject=f"Invitation à rejoindre {invitation.organization.name}",
            message=text_message,
            from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@example.com'),
            recipient_list=[invitation.email],
            html_message=html_message,
            fail_silently=False
        )

        logger.info(f"Invitation email sent successfully to {invitation.email}")

    except EmployeeInvitation.DoesNotExist:
        logger.error(f"Invitation {invitation_id} not found")
        # Don't retry if invitation doesn't exist
        return

    except Exception as exc:
        logger.error(f"Error sending invitation email to {invitation.email}: {exc}")

        # Retry with exponential backoff: 5min, 15min, 45min
        countdown = 300 * (3 ** self.request.retries)  # 300s, 900s, 2700s
        raise self.retry(exc=exc, countdown=countdown)
