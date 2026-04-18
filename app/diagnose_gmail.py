"""
Diagnostic complet de la connexion Gmail SMTP
"""
import smtplib
import os
from dotenv import load_dotenv

# Charger .env
env_path = '/mnt/data/Projets/loura/stack/backend/.env'
load_dotenv(env_path)

def test_gmail_smtp():
    """Test direct de connexion Gmail SMTP"""
    print("=" * 70)
    print("DIAGNOSTIC CONNEXION GMAIL SMTP")
    print("=" * 70)

    email = os.getenv('EMAIL_HOST_USER')
    password = os.getenv('EMAIL_HOST_PASSWORD')

    print(f"\n📧 Email: {email}")
    print(f"🔑 Mot de passe:")
    print(f"   - Longueur: {len(password)} caractères")
    print(f"   - Valeur: '{password}'")
    print(f"   - Premier car: '{password[0]}' (ASCII: {ord(password[0])})")
    print(f"   - Dernier car: '{password[-1]}' (ASCII: {ord(password[-1])})")
    print(f"   - Contient espaces: {' ' in password}")
    print(f"   - Sans espaces: '{password.replace(' ', '')}' ({len(password.replace(' ', ''))} car)")

    # Test 1 : Connexion avec mot de passe tel quel
    print("\n" + "=" * 70)
    print("TEST 1 : Connexion avec mot de passe tel quel")
    print("=" * 70)
    try:
        server = smtplib.SMTP('smtp.gmail.com', 587, timeout=10)
        server.set_debuglevel(1)  # Mode debug
        server.ehlo()
        server.starttls()
        server.ehlo()
        print(f"\nTentative de login avec: user='{email}', pass='{password}'")
        server.login(email, password)
        print("\n✅ SUCCÈS : Connexion réussie !")
        server.quit()
        return True
    except smtplib.SMTPAuthenticationError as e:
        print(f"\n❌ ÉCHEC : {e}")
        print("\nCode d'erreur 535 signifie: Identifiants invalides")
    except Exception as e:
        print(f"\n❌ ERREUR : {e}")

    # Test 2 : Sans espaces
    if ' ' in password:
        print("\n" + "=" * 70)
        print("TEST 2 : Connexion SANS espaces dans le mot de passe")
        print("=" * 70)
        password_no_space = password.replace(' ', '')
        try:
            server = smtplib.SMTP('smtp.gmail.com', 587, timeout=10)
            server.starttls()
            print(f"Tentative avec: '{password_no_space}'")
            server.login(email, password_no_space)
            print("\n✅ SUCCÈS : Le problème était les espaces !")
            server.quit()
            print(f"\n💡 SOLUTION : Utilisez dans .env :")
            print(f"EMAIL_HOST_PASSWORD={password_no_space}")
            return True
        except smtplib.SMTPAuthenticationError as e:
            print(f"\n❌ ÉCHEC : {e}")
        except Exception as e:
            print(f"\n❌ ERREUR : {e}")

    # Diagnostic final
    print("\n" + "=" * 70)
    print("DIAGNOSTIC")
    print("=" * 70)
    print("\n❌ Aucune configuration n'a fonctionné.")
    print("\n🔍 Causes possibles :")
    print("   1. Le mot de passe d'application Gmail est INCORRECT")
    print("   2. La validation en 2 étapes n'est PAS activée sur le compte")
    print("   3. Le mot de passe d'application a été RÉVOQUÉ")
    print("   4. Le compte Gmail a des restrictions de sécurité")
    print("\n✅ SOLUTIONS :")
    print("\n   A) Régénérer un NOUVEAU mot de passe d'application :")
    print("      1. Allez sur https://myaccount.google.com/apppasswords")
    print("      2. Supprimez l'ancien mot de passe 'Loura Backend'")
    print("      3. Créez-en un nouveau")
    print("      4. Copiez EXACTEMENT les 16 caractères")
    print("      5. Dans .env, mettez: EMAIL_HOST_PASSWORD=xxxxyyyyzzzzwwww")
    print("         (SANS espaces, SANS guillemets)")
    print("\n   B) Vérifier la validation en 2 étapes :")
    print("      - https://myaccount.google.com/security")
    print("      - 'Validation en deux étapes' doit être ACTIVÉE")
    print("\n   C) Mode console (test immédiat sans Gmail) :")
    print("      Dans .env, changez:")
    print("      EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend")
    print("\n" + "=" * 70)

    return False

if __name__ == '__main__':
    test_gmail_smtp()
