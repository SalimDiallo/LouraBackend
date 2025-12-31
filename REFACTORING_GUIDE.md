# 📖 Guide d'Utilisation - Code Refactorisé

**Version:** Phase 1
**Date:** 2025-12-27

Ce guide explique comment utiliser les nouveaux patterns et modules créés pendant le refactoring Phase 1.

---

## 📋 Table des Matières

1. [Créer un Nouveau Serializer](#créer-un-nouveau-serializer)
2. [Créer un Nouveau ViewSet](#créer-un-nouveau-viewset)
3. [Générer des Numéros de Documents](#générer-des-numéros-de-documents)
4. [Utiliser les Repositories](#utiliser-les-repositories)
5. [Extraire des Filtres](#extraire-des-filtres)
6. [Bonnes Pratiques](#bonnes-pratiques)

---

## 1. Créer un Nouveau Serializer

### Pattern de Base

```python
from rest_framework import serializers
from .models import MonModele
from .serializers_base import InventoryBaseSerializer

class MonModeleSerializer(InventoryBaseSerializer):
    """Serializer pour MonModele"""

    # Déclarer les champs SerializerMethodField
    id = serializers.SerializerMethodField()
    organization = serializers.SerializerMethodField()
    category = serializers.SerializerMethodField()  # Si vous avez une FK category

    # Champs personnalisés
    mon_champ_custom = serializers.SerializerMethodField()

    class Meta:
        model = MonModele
        fields = [
            'id', 'organization', 'category',
            'name', 'description', 'mon_champ_custom',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    # get_id, get_organization, get_category sont AUTOMATIQUEMENT hérités
    # Pas besoin de les redéfinir !

    # Seulement vos méthodes personnalisées
    def get_mon_champ_custom(self, obj):
        return obj.calculate_something()
```

### Champs UUID Automatiquement Disponibles

Héritant de `InventoryBaseSerializer`, vous avez accès à ces méthodes **sans les redéfinir** :

```python
get_id()              # UUID → string
get_organization()    # Organization UUID → string
get_product()         # Product UUID → string
get_warehouse()       # Warehouse UUID → string
get_category()        # Category UUID → string
get_supplier()        # Supplier UUID → string
get_customer()        # Customer UUID → string
get_order()           # Order UUID → string
get_sale()            # Sale UUID → string
get_movement()        # Movement UUID → string
get_parent()          # Parent UUID → string
get_user()            # User UUID → string
get_created_by()      # Created by UUID → string
get_updated_by()      # Updated by UUID → string
```

### Serializer pour les Listes (avec noms des relations)

```python
from .serializers_base import InventoryListSerializer

class MonModeleListSerializer(InventoryListSerializer):
    """Serializer léger pour les listes"""

    id = serializers.SerializerMethodField()
    category_name = serializers.SerializerMethodField()  # Nom de la catégorie

    class Meta:
        model = MonModele
        fields = ['id', 'name', 'category_name', 'is_active']

    # get_id ET get_category_name sont hérités automatiquement !
```

---

## 2. Créer un Nouveau ViewSet

### Pattern de Base avec Repository

```python
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from core.mixins import BaseOrganizationViewSetMixin

from .models import MonModele
from .serializers import MonModeleSerializer, MonModeleListSerializer
from .repositories import MonModeleRepository  # Créer votre repository
from .filters import QueryFilterExtractor
from .factories import DocumentNumberFactory

class MonModeleViewSet(BaseOrganizationViewSetMixin, viewsets.ModelViewSet):
    """
    ViewSet pour gérer MonModele
    """
    queryset = MonModele.objects.all()
    serializer_class = MonModeleSerializer
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        """Utiliser un serializer différent pour les listes"""
        if self.action == 'list':
            return MonModeleListSerializer
        return MonModeleSerializer

    def get_queryset(self):
        """
        Récupérer le queryset filtré.

        REFACTORED: Utilise QueryFilterExtractor et MonModeleRepository
        """
        organization = self.get_organization_from_request()
        extractor = QueryFilterExtractor(self.request.query_params)
        filters = extractor.extract_common_filters()  # ou votre méthode custom

        return MonModeleRepository.get_filtered(organization, filters)

    def perform_create(self, serializer):
        """
        Créer un objet avec numéro auto-généré.

        REFACTORED: Utilise DocumentNumberFactory
        """
        organization = self.get_organization_from_request()

        # Générer le numéro
        numero = DocumentNumberFactory.generate(
            model_class=MonModele,
            organization=organization,
            doc_type='mon_type',  # Voir DEFAULT_PREFIXES dans factories.py
            field_name='numero'
        )

        serializer.save(organization=organization, numero=numero)
```

### ViewSet Simple (sans Repository si pas nécessaire)

```python
class SimpleViewSet(BaseOrganizationViewSetMixin, viewsets.ModelViewSet):
    queryset = MonModele.objects.all()
    serializer_class = MonModeleSerializer
    permission_classes = [IsAuthenticated]

    # get_queryset() héritée de BaseOrganizationViewSetMixin suffit
    # Elle filtre automatiquement par organization
```

---

## 3. Générer des Numéros de Documents

### Utilisation de DocumentNumberFactory

```python
from .factories import DocumentNumberFactory
from .models import MonModele

# Générer un numéro avec préfixe par défaut
numero = DocumentNumberFactory.generate(
    model_class=MonModele,
    organization=organization,
    doc_type='sale',  # Utilise le préfixe 'VTE' par défaut
    field_name='numero'
)
# Résultat: "VTE-000001", "VTE-000002", etc.
```

### Préfixes Disponibles par Défaut

```python
DEFAULT_PREFIXES = {
    'order': 'CMN',           # Commandes
    'sale': 'VTE',            # Ventes
    'payment': 'REC',         # Paiements
    'receipt': 'REC',         # Reçus
    'proforma': 'PF',         # Proformas
    'invoice': 'INV',         # Factures
    'purchase_order': 'BC',   # Bons de commande
    'delivery': 'BL',         # Bons de livraison
    'expense': 'DEP',         # Dépenses
    'quote': 'DEV',           # Devis
    'credit_note': 'CN',      # Notes de crédit
    'debit_note': 'DN',       # Notes de débit
}
```

### Utiliser un Préfixe Personnalisé

```python
numero = DocumentNumberFactory.generate(
    model_class=MonModele,
    organization=organization,
    prefix='CUSTOM',  # Préfixe personnalisé
    field_name='numero',
    length=8,  # Longueur de la partie numérique (défaut: 6)
    separator='-'  # Séparateur (défaut: '-')
)
# Résultat: "CUSTOM-00000001"
```

### Générer plusieurs numéros en batch

```python
numeros = DocumentNumberFactory.generate_batch(
    model_class=MonModele,
    organization=organization,
    count=5,
    doc_type='sale'
)
# Résultat: ['VTE-000001', 'VTE-000002', 'VTE-000003', 'VTE-000004', 'VTE-000005']
```

---

## 4. Utiliser les Repositories

### Créer un Nouveau Repository

```python
# Dans app/inventory/repositories.py

from django.db.models import Q, Sum, F
from django.db.models.functions import Coalesce

class MonModeleRepository(BaseRepository):
    """Repository pour MonModele"""

    @classmethod
    def _get_model(cls):
        from .models import MonModele
        return MonModele

    model = property(_get_model)

    @classmethod
    def get_filtered(cls, organization, filters=None):
        """Récupérer les objets filtrés"""
        from .models import MonModele

        queryset = MonModele.objects.filter(organization=organization)

        if not filters:
            return queryset.select_related('organization')

        # Filtre par statut actif
        if 'is_active' in filters and filters['is_active'] is not None:
            queryset = queryset.filter(is_active=filters['is_active'])

        # Filtre par catégorie
        if 'category_id' in filters and filters['category_id']:
            queryset = queryset.filter(category_id=filters['category_id'])

        # Recherche textuelle
        if 'search' in filters and filters['search']:
            search_term = filters['search']
            queryset = queryset.filter(
                Q(name__icontains=search_term) |
                Q(code__icontains=search_term) |
                Q(description__icontains=search_term)
            )

        # Optimisation avec select_related et prefetch_related
        return queryset.select_related(
            'organization',
            'category'
        ).prefetch_related('items').order_by('-created_at')
```

### Méthodes du BaseRepository

Tous les repositories héritent de ces méthodes :

```python
# Récupérer par ID
obj = MonModeleRepository.get_by_id(pk='uuid-here', organization=org)

# Récupérer tous les objets
all_objects = MonModeleRepository.get_all(organization=org)

# Récupérer seulement les actifs
active_objects = MonModeleRepository.get_active(organization=org)

# Recherche
results = MonModeleRepository.search(
    organization=org,
    search_term='keyword',
    search_fields=['name', 'code', 'description']
)
```

---

## 5. Extraire des Filtres

### Utilisation de QueryFilterExtractor

```python
from .filters import QueryFilterExtractor

def get_queryset(self):
    organization = self.get_organization_from_request()

    # Créer l'extracteur
    extractor = QueryFilterExtractor(self.request.query_params)

    # Extraire les filtres selon le modèle
    filters = extractor.extract_product_filters()
    # Ou: extract_category_filters()
    # Ou: extract_order_filters()
    # Ou: extract_sale_filters()
    # etc.

    return ProductRepository.get_filtered(organization, filters)
```

### Méthodes d'Extraction Disponibles

```python
# Filtres communs (is_active, search, ordering)
filters = extractor.extract_common_filters()

# Filtres spécifiques
filters = extractor.extract_category_filters()
filters = extractor.extract_warehouse_filters()
filters = extractor.extract_supplier_filters()
filters = extractor.extract_product_filters()
filters = extractor.extract_order_filters()
filters = extractor.extract_stock_filters()
filters = extractor.extract_movement_filters()
filters = extractor.extract_sale_filters()
filters = extractor.extract_customer_filters()
```

### Créer une Méthode d'Extraction Personnalisée

```python
# Dans app/inventory/filters.py

class QueryFilterExtractor:
    # ... autres méthodes

    def extract_mon_modele_filters(self):
        """Extraire les filtres pour MonModele"""
        filters = self.extract_common_filters()  # is_active, search, ordering

        # Ajouter vos filtres spécifiques
        filters.update({
            'category_id': self.get_uuid('category'),
            'min_price': self.get_float('min_price'),
            'max_price': self.get_float('max_price'),
            'start_date': self.get_date('start_date'),
            'end_date': self.get_date('end_date'),
            'status': self.get_string('status'),
            'tags': self.get_list('tags'),  # Comma-separated
        })

        return filters
```

### Types de Convertisseurs Disponibles

```python
extractor = QueryFilterExtractor(request.query_params)

# Récupérer et convertir les paramètres
string_value = extractor.get_string('param_name')
int_value = extractor.get_int('param_name', default=0)
float_value = extractor.get_float('param_name', default=0.0)
bool_value = extractor.get_bool('param_name')  # Accepte 'true', '1', 'yes'
date_value = extractor.get_date('param_name')  # Format ISO
datetime_value = extractor.get_datetime('param_name')
uuid_value = extractor.get_uuid('param_name')
list_value = extractor.get_list('param_name')  # Comma-separated

# Vérifier la présence d'un paramètre
if extractor.has_param('special_param'):
    # Faire quelque chose
```

---

## 6. Bonnes Pratiques

### ✅ DO - À Faire

1. **Toujours hériter de InventoryBaseSerializer**
   ```python
   class MySerializer(InventoryBaseSerializer):
       # ✅ Bon
   ```

2. **Utiliser les Repositories pour les requêtes complexes**
   ```python
   def get_queryset(self):
       return MyRepository.get_filtered(organization, filters)
       # ✅ Bon - Réutilisable, testable, optimisé
   ```

3. **Utiliser DocumentNumberFactory pour TOUS les numéros**
   ```python
   numero = DocumentNumberFactory.generate(...)
   # ✅ Bon - Thread-safe, cohérent
   ```

4. **Utiliser QueryFilterExtractor pour extraire les filtres**
   ```python
   extractor = QueryFilterExtractor(request.query_params)
   filters = extractor.extract_product_filters()
   # ✅ Bon - Type-safe, centralisé
   ```

5. **Documenter les méthodes refactorisées**
   ```python
   def perform_create(self, serializer):
       """
       Créer un objet.

       REFACTORED: Utilise DocumentNumberFactory
       """
   ```

6. **Optimiser les requêtes avec select_related/prefetch_related**
   ```python
   return queryset.select_related('category', 'organization')
                  .prefetch_related('items')
   # ✅ Bon - Évite les N+1 queries
   ```

---

### ❌ DON'T - À Éviter

1. **Ne pas hériter de serializers.ModelSerializer directement**
   ```python
   class MySerializer(serializers.ModelSerializer):
       # ❌ Mauvais - Vous allez dupliquer les getters
   ```

2. **Ne pas dupliquer la logique de génération de numéros**
   ```python
   last = Model.objects.filter(...).order_by('-id').first()
   if last:
       num = int(last.number.split('-')[-1]) + 1
   # ❌ Mauvais - Utilisez DocumentNumberFactory
   ```

3. **Ne pas extraire manuellement les query params**
   ```python
   is_active = request.query_params.get('is_active')
   if is_active:
       is_active = is_active.lower() == 'true'
   # ❌ Mauvais - Utilisez QueryFilterExtractor
   ```

4. **Ne pas écrire de requêtes complexes dans les ViewSets**
   ```python
   def get_queryset(self):
       queryset = Model.objects.filter(organization=org)
       if param1:
           queryset = queryset.filter(...)
       if param2:
           queryset = queryset.filter(...)
       # ❌ Mauvais - Créez un Repository
   ```

5. **Ne pas oublier les optimisations de requêtes**
   ```python
   return Model.objects.filter(organization=org)
   # ❌ Mauvais - Pas de select_related, risque de N+1
   ```

---

## 🎯 Exemples Complets

### Exemple 1: Créer un Nouveau Module "Clients"

#### 1. Créer le Repository

```python
# Dans app/inventory/repositories.py

class ClientRepository(BaseRepository):
    @classmethod
    def _get_model(cls):
        from .models import Client
        return Client

    model = property(_get_model)

    @classmethod
    def get_filtered(cls, organization, filters=None):
        from .models import Client

        queryset = Client.objects.filter(organization=organization)

        if not filters:
            return queryset.select_related('organization')

        if 'is_active' in filters and filters['is_active'] is not None:
            queryset = queryset.filter(is_active=filters['is_active'])

        if 'search' in filters and filters['search']:
            queryset = queryset.filter(
                Q(name__icontains=filters['search']) |
                Q(email__icontains=filters['search'])
            )

        return queryset.select_related('organization').order_by('name')
```

#### 2. Créer le Serializer

```python
# Dans app/inventory/serializers.py

class ClientSerializer(InventoryBaseSerializer):
    id = serializers.SerializerMethodField()
    organization = serializers.SerializerMethodField()
    total_sales = serializers.SerializerMethodField()

    class Meta:
        model = Client
        fields = ['id', 'organization', 'name', 'email', 'phone', 'total_sales']

    # get_id et get_organization sont hérités

    def get_total_sales(self, obj):
        return obj.sales.count()
```

#### 3. Créer le ViewSet

```python
# Dans app/inventory/views.py

class ClientViewSet(BaseOrganizationViewSetMixin, viewsets.ModelViewSet):
    queryset = Client.objects.all()
    serializer_class = ClientSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        organization = self.get_organization_from_request()
        extractor = QueryFilterExtractor(self.request.query_params)
        filters = extractor.extract_common_filters()
        return ClientRepository.get_filtered(organization, filters)

    def perform_create(self, serializer):
        organization = self.get_organization_from_request()
        client_number = DocumentNumberFactory.generate(
            model_class=Client,
            organization=organization,
            prefix='CLT',
            field_name='client_number'
        )
        serializer.save(organization=organization, client_number=client_number)
```

#### 4. Enregistrer l'URL

```python
# Dans app/inventory/urls.py

from .views import ClientViewSet

router.register(r'clients', ClientViewSet, basename='client')
```

**C'est tout ! 🎉**

Vous avez maintenant un module complet :
- ✅ Génération automatique de numéros (CLT-000001, etc.)
- ✅ Filtrage et recherche
- ✅ Optimisation des requêtes
- ✅ Code réutilisable et maintenable

---

## 📞 Support

Si vous avez des questions ou rencontrez des problèmes :

1. Consultez d'abord `REFACTORING_PHASE1_SUMMARY.md`
2. Regardez les exemples dans le code existant (CategoryViewSet, ProductSerializer, etc.)
3. Vérifiez les docstrings dans les modules (`serializers_base.py`, `factories.py`, etc.)

---

**Bonne chance avec le refactoring ! 🚀**
