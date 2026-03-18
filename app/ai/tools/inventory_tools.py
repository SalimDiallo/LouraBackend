"""
AI Tools - Inventory & Sales Module
====================================
Outils pour l'inventaire, les ventes, et les clients.
"""

from ai.tools.registry import register_tool


@register_tool(
    name="liste_produits",
    description="Liste les produits en stock avec leurs informations (nom, SKU, catégorie, prix, stock). Utilise cet outil quand l'utilisateur demande la liste des produits ou cherche un produit.",
    category="inventory",
    parameters={
        "type": "object",
        "properties": {
            "search": {
                "type": "string",
                "description": "Terme de recherche pour filtrer par nom ou SKU"
            },
            "category": {
                "type": "string",
                "description": "Filtrer par catégorie"
            },
            "low_stock_only": {
                "type": "boolean",
                "description": "Si true, affiche uniquement les produits en stock bas"
            },
            "limit": {
                "type": "integer",
                "description": "Nombre maximum de résultats (défaut: 20)",
                "default": 20
            }
        },
        "required": [],
    },
)
def list_products(organization, search: str = None, category: str = None,
                  low_stock_only: bool = False, limit: int = 20) -> dict:
    """Liste les produits."""
    from inventory.models import Product, Stock
    from django.db.models import Q, Sum

    qs = Product.objects.filter(organization=organization)

    if search:
        qs = qs.filter(Q(name__icontains=search) | Q(sku__icontains=search))

    if category:
        qs = qs.filter(category__name__icontains=category)

    products = qs.select_related('category')[:limit]

    results = []
    for p in products:
        total_stock = Stock.objects.filter(product=p).aggregate(
            total=Sum('quantity')
        )['total'] or 0

        if low_stock_only and p.min_stock_level and total_stock > p.min_stock_level:
            continue

        results.append({
            "id": str(p.id),
            "nom": p.name,
            "sku": p.sku or "",
            "categorie": p.category.name if p.category else "Non catégorisé",
            "prix_vente": float(p.selling_price) if p.selling_price else 0,
            "stock_total": total_stock,
            "stock_minimum": p.min_stock_level or 0,
            "alerte_stock": total_stock <= p.min_stock_level if p.min_stock_level else False,
        })

    return {
        "total": len(results),
        "produits": results,
    }


@register_tool(
    name="statistiques_ventes",
    description="Donne les statistiques de ventes : chiffre d'affaires, nombre de ventes, panier moyen sur une période donnée. Utilise cet outil quand l'utilisateur demande les ventes, le CA, ou un résumé commercial.",
    category="inventory",
    parameters={
        "type": "object",
        "properties": {
            "days": {
                "type": "integer",
                "description": "Nombre de jours à analyser (défaut: 30)",
                "default": 30
            }
        },
        "required": [],
    },
)
def get_sales_stats(organization, days: int = 30) -> dict:
    """Statistiques des ventes."""
    from inventory.models import Sale
    from django.utils import timezone
    from django.db.models import Sum, Count, Avg

    start_date = timezone.now() - timezone.timedelta(days=days)
    sales = Sale.objects.filter(
        organization=organization,
        created_at__gte=start_date,
    )

    stats = sales.aggregate(
        total_ca=Sum('total_amount'),
        nombre_ventes=Count('id'),
        panier_moyen=Avg('total_amount'),
    )

    return {
        "periode_jours": days,
        "chiffre_affaires": float(stats['total_ca'] or 0),
        "nombre_ventes": stats['nombre_ventes'] or 0,
        "panier_moyen": round(float(stats['panier_moyen'] or 0), 2),
    }


@register_tool(
    name="ventes_recentes",
    description="Liste les ventes récentes avec les détails (client, montant, statut, date). Utilise cet outil quand l'utilisateur demande les dernières ventes ou transactions.",
    category="inventory",
    parameters={
        "type": "object",
        "properties": {
            "limit": {
                "type": "integer",
                "description": "Nombre de ventes à afficher (défaut: 10)",
                "default": 10
            }
        },
        "required": [],
    },
)
def get_recent_sales(organization, limit: int = 10) -> dict:
    """Ventes récentes."""
    from inventory.models import Sale

    sales = Sale.objects.filter(
        organization=organization,
    ).select_related('customer').order_by('-created_at')[:limit]

    results = []
    for s in sales:
        results.append({
            "numero": s.sale_number,
            "client": s.customer.name if s.customer else "Anonyme",
            "montant_total": float(s.total_amount),
            "statut": s.status,
            "date": str(s.created_at.date()),
        })

    return {
        "total": len(results),
        "ventes": results,
    }


@register_tool(
    name="liste_clients",
    description="Liste les clients de l'organisation. Utilise cet outil quand l'utilisateur demande la liste des clients ou cherche un client.",
    category="inventory",
    parameters={
        "type": "object",
        "properties": {
            "search": {
                "type": "string",
                "description": "Terme de recherche pour filtrer par nom, email ou téléphone"
            },
        },
        "required": [],
    },
)
def list_customers(organization, search: str = None) -> dict:
    """Liste les clients."""
    from inventory.models import Customer
    from django.db.models import Q

    qs = Customer.objects.filter(organization=organization)

    if search:
        qs = qs.filter(
            Q(name__icontains=search) |
            Q(email__icontains=search) |
            Q(phone__icontains=search)
        )

    customers = qs[:20]

    results = []
    for c in customers:
        results.append({
            "id": str(c.id),
            "nom": c.name,
            "email": c.email or "",
            "telephone": c.phone or "",
        })

    return {
        "total": len(results),
        "clients": results,
    }


@register_tool(
    name="clients_avec_dettes",
    description=(
        "Liste les clients qui ont des ventes à crédit impayées (dettes). "
        "Utilise cet outil quand l'utilisateur demande qui lui doit de l'argent, "
        "les créances, les dettes clients, ou les ventes à crédit."
    ),
    category="inventory",
    parameters={
        "type": "object",
        "properties": {},
        "required": [],
    },
)
def get_customers_with_debts(organization) -> dict:
    """Clients avec des dettes (ventes à crédit impayées)."""
    from inventory.models import Sale
    from django.db.models import Sum, F, Q

    # Trouver les ventes avec solde restant
    sales_with_debt = Sale.objects.filter(
        organization=organization,
        customer__isnull=False,
    ).exclude(
        status='cancelled',
    ).filter(
        Q(payment_status='partial') | Q(payment_status='unpaid'),
    ).select_related('customer')

    # Agréger par client
    clients_debts = {}
    for sale in sales_with_debt:
        client_name = sale.customer.name
        if client_name not in clients_debts:
            clients_debts[client_name] = {
                "client": client_name,
                "email": sale.customer.email or "",
                "telephone": sale.customer.phone or "",
                "total_du": 0,
                "nombre_ventes_impayees": 0,
                "ventes": [],
            }
        remaining = float(sale.total_amount) - float(getattr(sale, 'paid_amount', 0) or 0)
        clients_debts[client_name]["total_du"] += remaining
        clients_debts[client_name]["nombre_ventes_impayees"] += 1
        clients_debts[client_name]["ventes"].append({
            "numero": sale.sale_number,
            "montant": float(sale.total_amount),
            "restant": remaining,
            "date": str(sale.created_at.date()),
        })

    results = sorted(clients_debts.values(), key=lambda x: x["total_du"], reverse=True)

    total_debts = sum(c["total_du"] for c in results)

    return {
        "total_creances": total_debts,
        "nombre_clients": len(results),
        "clients": results[:15],
    }
