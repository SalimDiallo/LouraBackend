"""
Script de test pour l'envoi d'email d'invitation
"""
import os
import sys
import django
from datetime import timedelta

# Setup Django
sys.path.insert(0, os.path.dirname(__file__))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'lourabackend.settings')
django.setup()

from django.utils import timezone
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings

def test_invitation_email():
    """Test de rendu et d'envoi d'email d'invitation"""
    print("=" * 70)
    print("TEST EMAIL D'INVITATION")
    print("=" * 70)

    # Données de test
    context = {
        'invitation': type('obj', (object,), {
            'first_name': 'John',
            'email': 'test@example.com',
            'invitation_message': 'Bienvenue dans notre équipe !',
        })(),
        'organization_name': 'Loura Test',
        'inviter_name': 'Admin Test',
        'invitation_url': 'http://localhost:3000/invite/accept/test-token-123',
        'expires_at': timezone.now() + timedelta(days=7),
        'role_name': 'Employé',
        'days_until_expiry': 7,
    }

    print("\n1️⃣  Test de rendu des templates...")

    # Test template TXT
    try:
        txt_message = render_to_string('emails/employee_invitation.txt', context)
        print("   ✅ Template TXT rendu avec succès")
        print(f"   Longueur: {len(txt_message)} caractères")
    except Exception as e:
        print(f"   ❌ Erreur template TXT: {e}")
        return

    # Test template HTML
    try:
        html_message = render_to_string('emails/employee_invitation.html', context)
        print("   ✅ Template HTML rendu avec succès")
        print(f"   Longueur: {len(html_message)} caractères")
    except Exception as e:
        print(f"   ❌ Erreur template HTML: {e}")
        html_message = None

    print("\n2️⃣  Configuration email:")
    print(f"   Backend: {settings.EMAIL_BACKEND}")
    print(f"   Host: {settings.EMAIL_HOST}")
    print(f"   Port: {settings.EMAIL_PORT}")
    print(f"   From: {settings.DEFAULT_FROM_EMAIL}")

    print("\n3️⃣  Envoi de l'email de test...")
    try:
        send_mail(
            subject=f"Invitation à rejoindre {context['organization_name']}",
            message=txt_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[settings.EMAIL_HOST_USER],  # Envoyer à soi-même
            html_message=html_message,
            fail_silently=False
        )
        print("   ✅ Email envoyé avec succès !")
        print(f"   📧 Vérifiez votre boîte: {settings.EMAIL_HOST_USER}")
    except Exception as e:
        print(f"   ❌ Erreur lors de l'envoi: {e}")
        import traceback
        traceback.print_exc()

    print("\n" + "=" * 70)

if __name__ == '__main__':
    test_invitation_email()
