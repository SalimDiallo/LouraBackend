"""
Script de test pour vérifier la configuration email
"""
import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.dirname(__file__))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'lourabackend.settings')
django.setup()

from django.core.mail import send_mail
from django.conf import settings

def test_email():
    """Test simple d'envoi d'email"""
    print("=" * 60)
    print("TEST CONFIGURATION EMAIL")
    print("=" * 60)
    print(f"\nEMAIL_BACKEND: {settings.EMAIL_BACKEND}")
    print(f"EMAIL_HOST: {settings.EMAIL_HOST}")
    print(f"EMAIL_PORT: {settings.EMAIL_PORT}")
    print(f"EMAIL_USE_TLS: {settings.EMAIL_USE_TLS}")
    print(f"EMAIL_HOST_USER: {settings.EMAIL_HOST_USER}")
    print(f"EMAIL_HOST_PASSWORD: {'*' * 10 if settings.EMAIL_HOST_PASSWORD else '(vide)'}")
    print(f"DEFAULT_FROM_EMAIL: {settings.DEFAULT_FROM_EMAIL}")
    print("\n" + "=" * 60)

    try:
        print("\nEnvoi d'un email de test...")
        send_mail(
            subject='Test Email - Loura Backend',
            message='Ceci est un email de test pour vérifier la configuration Gmail SMTP.',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[settings.EMAIL_HOST_USER],  # Envoyer à soi-même
            fail_silently=False,
        )
        print("✅ Email envoyé avec succès !")
        print(f"📧 Vérifiez votre boîte email: {settings.EMAIL_HOST_USER}")

    except Exception as e:
        print(f"❌ Erreur lors de l'envoi: {e}")
        print(f"\nType d'erreur: {type(e).__name__}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    test_email()
