"""
Utilitaires pour la gestion automatique des alertes de stock.
"""

from django.utils import timezone
from django.db.models import Sum

from .models import Alert, Product, Stock


def check_and_update_stock_alert(product, warehouse=None):
    """
    Vérifie le niveau de stock d'un produit et crée/résout automatiquement les alertes.
    
    Args:
        product: Instance du produit à vérifier
        warehouse: Instance de l'entrepôt (optionnel, si None vérifie le stock total)
    
    Returns:
        dict: {'action': 'created'|'resolved'|'none', 'alert': Alert|None}
    """
    if not product or not product.is_active:
        return {'action': 'none', 'alert': None}
    
    # Calculer le stock
    if warehouse:
        stock = Stock.objects.filter(product=product, warehouse=warehouse).first()
        current_quantity = stock.quantity if stock else 0
    else:
        current_quantity = product.stocks.aggregate(total=Sum('quantity'))['total'] or 0
    
    min_level = product.min_stock_level or 0
    
    # Chercher une alerte existante non résolue
    existing_alert = Alert.objects.filter(
        product=product,
        warehouse=warehouse,
        alert_type__in=['low_stock', 'out_of_stock'],
        is_resolved=False
    ).first()
    
    # Cas 1: Stock OK et alerte existante → résoudre
    if current_quantity > min_level and existing_alert:
        existing_alert.is_resolved = True
        existing_alert.resolved_at = timezone.now()
        existing_alert.save()
        return {'action': 'resolved', 'alert': existing_alert}
    
    # Cas 2: Stock faible/rupture et pas d'alerte → créer
    if current_quantity <= min_level and not existing_alert:
        if current_quantity <= 0:
            alert_type = 'out_of_stock'
            severity = 'critical'
            message = f"Rupture de stock: {product.name}"
        else:
            alert_type = 'low_stock'
            severity = 'high'
            message = f"Stock faible: {product.name} ({current_quantity} {product.get_unit_display()})"
        
        alert = Alert.objects.create(
            organization=product.organization,
            product=product,
            warehouse=warehouse,
            alert_type=alert_type,
            severity=severity,
            message=message
        )
        return {'action': 'created', 'alert': alert}
    
    # Cas 3: Mise à jour du type d'alerte si le stock a encore baissé
    if existing_alert and current_quantity <= 0 and existing_alert.alert_type == 'low_stock':
        existing_alert.alert_type = 'out_of_stock'
        existing_alert.severity = 'critical'
        existing_alert.message = f"Rupture de stock: {product.name}"
        existing_alert.save()
        return {'action': 'updated', 'alert': existing_alert}
    
    return {'action': 'none', 'alert': existing_alert}


def check_all_products_alerts(organization):
    """
    Vérifie les alertes pour tous les produits actifs d'une organisation.
    Utilisé pour la génération en masse.
    
    Returns:
        dict: {'created': int, 'resolved': int}
    """
    created_count = 0
    resolved_count = 0
    
    products = Product.objects.filter(
        organization=organization,
        is_active=True,
        min_stock_level__gt=0  # Seulement les produits avec un seuil défini
    )
    
    for product in products:
        result = check_and_update_stock_alert(product)
        if result['action'] == 'created':
            created_count += 1
        elif result['action'] == 'resolved':
            resolved_count += 1
    
    return {'created': created_count, 'resolved': resolved_count}
