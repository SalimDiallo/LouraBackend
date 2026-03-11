"""
Utilitaires pour la gestion automatique des alertes de stock.
"""

from django.utils import timezone
from django.db.models import Sum
from decimal import Decimal
from datetime import timedelta

from .models import Alert, Product, Stock


def check_and_update_stock_alert(product, warehouse=None):
    """
    Vérifie le niveau de stock d'un produit et crée/résout automatiquement les alertes.
    Système à 3 niveaux :
    - stock_warning (medium) : stock entre min_stock et min_stock + 5
    - low_stock (high) : stock <= min_stock mais > 0
    - out_of_stock (critical) : stock = 0

    Args:
        product: Instance du produit à vérifier
        warehouse: Instance de l'entrepôt (optionnel, si None vérifie le stock total)

    Returns:
        dict: {'action': 'created'|'resolved'|'updated'|'none', 'alert': Alert|None}
    """
    if not product or not product.is_active:
        return {'action': 'none', 'alert': None}

    # Calculer le stock actuel
    if warehouse:
        stock = Stock.objects.filter(product=product, warehouse=warehouse).first()
        current_quantity = Decimal(str(stock.quantity)) if stock else Decimal('0')
    else:
        total = product.stocks.aggregate(total=Sum('quantity'))['total']
        current_quantity = Decimal(str(total)) if total else Decimal('0')

    min_level = Decimal(str(product.min_stock_level)) if product.min_stock_level else Decimal('0')
    max_level = Decimal(str(product.max_stock_level)) if product.max_stock_level else Decimal('0')
    warning_threshold = min_level + Decimal('5')  # Seuil d'avertissement

    # Chercher une alerte de stock existante non résolue
    existing_alert = Alert.objects.filter(
        product=product,
        warehouse=warehouse,
        alert_type__in=['stock_warning', 'low_stock', 'out_of_stock'],
        is_resolved=False
    ).first()

    # Déterminer le type d'alerte nécessaire
    required_alert = None

    if current_quantity <= 0:
        required_alert = {
            'type': 'out_of_stock',
            'severity': 'critical',
            'message': f"🚨 Rupture de stock: {product.name}"
        }
    elif current_quantity <= min_level and min_level > 0:
        required_alert = {
            'type': 'low_stock',
            'severity': 'high',
            'message': f"⚠️ Stock critique: {product.name} ({float(current_quantity)} {product.get_unit_display()}, seuil: {float(min_level)})"
        }
    elif current_quantity <= warning_threshold and min_level > 0:
        required_alert = {
            'type': 'stock_warning',
            'severity': 'medium',
            'message': f"⚡ Stock bas: {product.name} ({float(current_quantity)} {product.get_unit_display()}, seuil recommandé: {float(warning_threshold)})"
        }

    # Cas 1: Stock OK et alerte existante → résoudre
    if not required_alert and existing_alert:
        existing_alert.is_resolved = True
        existing_alert.resolved_at = timezone.now()
        existing_alert.save()
        return {'action': 'resolved', 'alert': existing_alert}

    # Cas 2: Alerte nécessaire mais pas d'alerte existante → créer
    if required_alert and not existing_alert:
        alert = Alert.objects.create(
            organization=product.organization,
            product=product,
            warehouse=warehouse,
            alert_type=required_alert['type'],
            severity=required_alert['severity'],
            message=required_alert['message']
        )

        # Notification
        _send_alert_notification(product.organization, product, required_alert['type'],
                                required_alert['severity'], required_alert['message'], warehouse)

        return {'action': 'created', 'alert': alert}

    # Cas 3: Mise à jour du type d'alerte si le niveau a changé
    if required_alert and existing_alert and existing_alert.alert_type != required_alert['type']:
        existing_alert.alert_type = required_alert['type']
        existing_alert.severity = required_alert['severity']
        existing_alert.message = required_alert['message']
        existing_alert.save()

        # Notification pour escalade (warning -> low -> out)
        if required_alert['severity'] in ['high', 'critical']:
            _send_alert_notification(product.organization, product, required_alert['type'],
                                    required_alert['severity'], required_alert['message'], warehouse)

        return {'action': 'updated', 'alert': existing_alert}

    # Vérifier aussi le surstock si max_level est défini
    if max_level > 0:
        check_overstock_alert(product, warehouse, current_quantity, max_level)

    return {'action': 'none', 'alert': existing_alert}


def check_overstock_alert(product, warehouse, current_quantity, max_level):
    """
    Vérifie et crée une alerte de surstock si nécessaire.
    """
    existing_overstock = Alert.objects.filter(
        product=product,
        warehouse=warehouse,
        alert_type='overstock',
        is_resolved=False
    ).first()

    if current_quantity > max_level and not existing_overstock:
        Alert.objects.create(
            organization=product.organization,
            product=product,
            warehouse=warehouse,
            alert_type='overstock',
            severity='low',
            message=f"📦 Surstock: {product.name} ({float(current_quantity)} > {float(max_level)} {product.get_unit_display()})"
        )
        return True
    elif current_quantity <= max_level and existing_overstock:
        existing_overstock.is_resolved = True
        existing_overstock.resolved_at = timezone.now()
        existing_overstock.save()
        return True

    return False


def check_high_value_low_stock_alert(organization):
    """
    Détecte les produits de haute valeur avec un stock faible.
    Produit de haute valeur = selling_price > 100000 (à adapter selon le contexte)
    """
    from decimal import Decimal

    HIGH_VALUE_THRESHOLD = Decimal('100000')  # Ajuster selon la devise

    high_value_products = Product.objects.filter(
        organization=organization,
        is_active=True,
        selling_price__gte=HIGH_VALUE_THRESHOLD,
        min_stock_level__gt=0
    )

    created_count = 0

    for product in high_value_products:
        total_stock = product.stocks.aggregate(total=Sum('quantity'))['total'] or 0
        total_stock = Decimal(str(total_stock))
        min_level = Decimal(str(product.min_stock_level))

        existing_alert = Alert.objects.filter(
            product=product,
            warehouse=None,
            alert_type='high_value_low_stock',
            is_resolved=False
        ).first()

        if total_stock <= min_level and not existing_alert:
            Alert.objects.create(
                organization=organization,
                product=product,
                warehouse=None,
                alert_type='high_value_low_stock',
                severity='high',
                message=f"💎 Produit de valeur en stock faible: {product.name} ({float(total_stock)} unités, valeur: {float(product.selling_price)} GNF)"
            )
            created_count += 1
        elif total_stock > min_level and existing_alert:
            existing_alert.is_resolved = True
            existing_alert.resolved_at = timezone.now()
            existing_alert.save()

    return created_count


def check_no_movement_alert(organization, days_threshold=30):
    """
    Détecte les produits sans mouvement depuis X jours.
    """
    from .models import Movement

    threshold_date = timezone.now() - timedelta(days=days_threshold)

    products_with_stock = Product.objects.filter(
        organization=organization,
        is_active=True
    ).annotate(
        total_stock=Sum('stocks__quantity')
    ).filter(total_stock__gt=0)

    created_count = 0

    for product in products_with_stock:
        # Vérifier le dernier mouvement
        last_movement = Movement.objects.filter(
            product=product,
            organization=organization
        ).order_by('-movement_date').first()

        if not last_movement or last_movement.movement_date < threshold_date:
            existing_alert = Alert.objects.filter(
                product=product,
                warehouse=None,
                alert_type='no_movement',
                is_resolved=False
            ).first()

            if not existing_alert:
                days_ago = (timezone.now() - last_movement.movement_date).days if last_movement else "∞"
                Alert.objects.create(
                    organization=organization,
                    product=product,
                    warehouse=None,
                    alert_type='no_movement',
                    severity='low',
                    message=f"💤 Aucun mouvement: {product.name} (dernier mouvement il y a {days_ago} jours)"
                )
                created_count += 1

    return created_count


def _send_alert_notification(organization, product, alert_type, severity, message, warehouse):
    """Helper pour envoyer les notifications."""
    try:
        from notifications.notification_helpers import send_alert_notification
        send_alert_notification(
            organization=organization,
            product=product,
            alert_type=alert_type,
            severity=severity,
            message=message,
            warehouse=warehouse,
        )
    except Exception:
        pass  # La notification ne doit jamais bloquer la logique métier


def check_all_products_alerts(organization):
    """
    Vérifie toutes les alertes pour tous les produits actifs d'une organisation.
    Inclut les alertes de stock (warning, low, out), surstock, produits de valeur, et produits inactifs.
    Utilisé pour la génération en masse.

    Returns:
        dict: {'created': int, 'resolved': int, 'updated': int}
    """
    created_count = 0
    resolved_count = 0
    updated_count = 0

    # 1. Vérifier les alertes de stock standard pour tous les produits
    products = Product.objects.filter(
        organization=organization,
        is_active=True
    )

    for product in products:
        result = check_and_update_stock_alert(product)
        if result['action'] == 'created':
            created_count += 1
        elif result['action'] == 'resolved':
            resolved_count += 1
        elif result['action'] == 'updated':
            updated_count += 1

    # 2. Vérifier les produits de haute valeur avec stock faible
    high_value_count = check_high_value_low_stock_alert(organization)
    created_count += high_value_count

    # 3. Vérifier les produits sans mouvement (30 jours)
    no_movement_count = check_no_movement_alert(organization, days_threshold=30)
    created_count += no_movement_count

    return {
        'created': created_count,
        'resolved': resolved_count,
        'updated': updated_count
    }
