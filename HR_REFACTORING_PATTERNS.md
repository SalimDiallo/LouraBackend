# 🏢 HR Module - Design Patterns de Refactoring

**Source:** `hr/views_refactored.py` (fichier de démonstration)
**Date:** 2025-12-27
**Statut:** Documentation de référence

---

## 📋 Introduction

Ce document présente des exemples de refactoring pour le module HR en utilisant des design patterns avancés :
- **Service Layer Pattern** - Séparation de la logique métier
- **Mixin Pattern** - Réutilisation de comportements
- **Single Responsibility Principle** - Une classe, une responsabilité

---

## 🎯 Patterns Disponibles dans HR

### Mixins Disponibles

Le module HR dispose des mixins suivants (dans `hr/mixins.py`) :

| Mixin | Responsabilité | Méthodes Fournies |
|-------|---------------|-------------------|
| **HRViewSetMixin** | Filtrage par organization | `get_organization_from_request()` |
| **EmployeeRelatedMixin** | Filtrage via employee__organization | `get_queryset()` |
| **ApprovableMixin** | Actions approve/reject | `approve()`, `reject()`, `_do_approve()`, `_do_reject()` |
| **PDFExportMixin** | Export PDF générique | `export_pdf()`, `_get_pdf_filename()` |

### Services Disponibles

Le module HR dispose des services suivants (dans `hr/services.py`) :

| Service | Responsabilité | Méthodes Clés |
|---------|---------------|---------------|
| **EmployeeService** | Logique métier employés | `get_employee_stats()` |
| **LeaveService** | Gestion des congés | `create_leave_request()`, `approve_leave_request()`, `reject_leave_request()`, `get_organization_leave_stats()` |
| **PayrollService** | Gestion de la paie | `generate_payslips_for_period()`, `process_payroll_period()`, `close_payroll_period()`, `get_organization_payroll_stats()` |

---

## 💡 Exemples de Refactoring

### Exemple 1: EmployeeViewSet

#### Avant (Pattern classique)

```python
class EmployeeViewSet(BaseOrganizationViewSetMixin, viewsets.ModelViewSet):
    """ViewSet classique - ~150 lignes"""

    queryset = Employee.objects.all()
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.action == 'create':
            return EmployeeCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return EmployeeUpdateSerializer
        elif self.action == 'list':
            return EmployeeListSerializer
        return EmployeeSerializer

    @action(detail=False, methods=['get'])
    def stats(self, request):
        organization = self.get_organization_from_request()

        # Logique métier mélangée avec la présentation
        total = Employee.objects.filter(organization=organization).count()
        active = Employee.objects.filter(organization=organization, is_active=True).count()
        inactive = total - active

        # Calculs complexes
        by_department = Employee.objects.filter(
            organization=organization
        ).values('department__name').annotate(count=Count('id'))

        return Response({
            'total': total,
            'active': active,
            'inactive': inactive,
            'by_department': list(by_department)
        })
```

**Problèmes:**
- ❌ Logique métier dans le ViewSet
- ❌ Difficilement testable
- ❌ Duplication de code pour les stats
- ❌ Requêtes multiples non optimisées

---

#### Après (Avec Service Layer)

```python
class EmployeeViewSetRefactored(HRViewSetMixin, viewsets.ModelViewSet):
    """
    ViewSet refactorisé - ~50 lignes (70% de réduction)

    Utilise:
    - HRViewSetMixin pour le filtrage par organisation
    - EmployeeService pour la logique métier
    """
    queryset = Employee.objects.all()
    permission_classes = [IsAdminUserOrEmployee, RequiresEmployeePermission]

    # Configuration du mixin
    organization_field = 'organization'
    view_permission = 'can_view_employee'
    create_permission = 'can_create_employee'
    activation_permission = 'can_activate_employee'

    def get_serializer_class(self):
        """Choisit le serializer selon l'action."""
        serializer_map = {
            'create': EmployeeCreateSerializer,
            'update': EmployeeUpdateSerializer,
            'partial_update': EmployeeUpdateSerializer,
            'list': EmployeeListSerializer,
        }
        return serializer_map.get(self.action, EmployeeSerializer)

    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Retourne les statistiques des employés."""
        organization = self.get_organization_from_request(raise_exception=False)
        if not organization:
            return Response({
                'error': 'Organisation requise'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Délégation au service
        stats = EmployeeService.get_employee_stats(organization)
        return Response(stats)
```

**Avantages:**
- ✅ Logique métier séparée dans `EmployeeService`
- ✅ ViewSet réduit de 70% (~50 lignes vs ~150)
- ✅ Testable indépendamment (service + view)
- ✅ Réutilisable (stats disponibles ailleurs)
- ✅ Pattern Mapping pour les serializers

---

### Exemple 2: LeaveRequestViewSet

#### Avant (Pattern classique)

```python
class LeaveRequestViewSet(viewsets.ModelViewSet):
    """ViewSet classique - ~200 lignes"""

    queryset = LeaveRequest.objects.all()
    serializer_class = LeaveRequestSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user

        if isinstance(user, Employee):
            queryset = queryset.filter(employee__organization=user.organization)
        elif isinstance(user, AdminUser):
            queryset = queryset.filter(employee__organization__admin=user)

        return queryset

    def perform_create(self, serializer):
        # 40+ lignes de logique de création
        employee = serializer.validated_data['employee']
        leave_type = serializer.validated_data['leave_type']
        start_date = serializer.validated_data['start_date']
        end_date = serializer.validated_data['end_date']

        # Calcul des jours
        days = (end_date - start_date).days + 1

        # Vérification du solde
        balance = LeaveBalance.objects.get(
            employee=employee,
            leave_type=leave_type
        )
        if balance.balance < days:
            raise ValidationError("Solde insuffisant")

        # Création
        serializer.save()

    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        # 30+ lignes de logique d'approbation
        leave_request = self.get_object()

        if leave_request.status != 'pending':
            return Response({'error': 'Impossible d\'approuver'}, status=400)

        leave_request.status = 'approved'
        leave_request.approved_by = request.user
        leave_request.approval_date = timezone.now()
        leave_request.approval_notes = request.data.get('notes', '')
        leave_request.save()

        # Déduction du solde
        balance = LeaveBalance.objects.get(
            employee=leave_request.employee,
            leave_type=leave_request.leave_type
        )
        balance.balance -= leave_request.days
        balance.save()

        return Response({'message': 'Approuvé'})

    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        # 20+ lignes similaires
        ...

    @action(detail=True, methods=['get'])
    def export_pdf(self, request, pk=None):
        # 30+ lignes de génération PDF
        ...
```

**Problèmes:**
- ❌ 200+ lignes dans un seul ViewSet
- ❌ Logique métier complexe mélangée
- ❌ Code dupliqué (approve/reject)
- ❌ Difficile à tester
- ❌ Difficile à maintenir

---

#### Après (Avec Mixins + Service Layer)

```python
class LeaveRequestViewSetRefactored(
    EmployeeRelatedMixin,      # Filtrage par organization
    ApprovableMixin,            # Actions approve/reject
    PDFExportMixin,             # Export PDF
    HRViewSetMixin,             # Base HR
    viewsets.ModelViewSet
):
    """
    ViewSet refactorisé - ~80 lignes (60% de réduction)

    Utilise:
    - EmployeeRelatedMixin pour le filtrage par employee__organization
    - ApprovableMixin pour les actions approve/reject
    - PDFExportMixin pour l'export PDF
    - LeaveService pour la logique métier
    """
    queryset = LeaveRequest.objects.all()
    serializer_class = LeaveRequestSerializer
    permission_classes = [IsAdminUserOrEmployee, RequiresLeavePermission]

    # Configuration des mixins
    view_permission = 'can_view_leave'
    create_permission = 'can_create_leave'
    approval_permission = 'can_approve_leave'

    # Configuration PDF
    pdf_filename_template = 'Conge_{employee}_{date}.pdf'

    @property
    def pdf_generator_func(self):
        """Importer le générateur PDF à la demande."""
        from hr.pdf_generator import generate_leave_request_pdf
        return generate_leave_request_pdf

    def _get_pdf_filename(self, obj):
        """Génère le nom du fichier PDF pour une demande de congé."""
        employee_name = obj.employee.get_full_name().replace(' ', '_')
        date_str = obj.start_date.strftime('%Y%m%d')
        return f'Conge_{employee_name}_{date_str}.pdf'

    def perform_create(self, serializer):
        """Crée une demande de congé via le service."""
        user = self.request.user

        if isinstance(user, Employee):
            if not user.has_permission('can_create_leave'):
                raise ValidationError({'permission': 'Permission refusée'})

            # Délégation au service
            leave_request = LeaveService.create_leave_request(
                employee=user,
                leave_type=serializer.validated_data['leave_type'],
                start_date=serializer.validated_data['start_date'],
                end_date=serializer.validated_data['end_date'],
                reason=serializer.validated_data.get('reason', ''),
                start_half_day=serializer.validated_data.get('start_half_day', False),
                end_half_day=serializer.validated_data.get('end_half_day', False),
            )
            serializer.instance = leave_request

    def _do_approve(self, obj, request):
        """Approuve une demande de congé via le service."""
        notes = request.data.get('approval_notes', '')
        success = LeaveService.approve_leave_request(obj, request.user, notes)

        if success:
            return Response({'message': 'Demande approuvée'})
        return Response({
            'message': 'Impossible d\'approuver cette demande'
        }, status=status.HTTP_400_BAD_REQUEST)

    def _do_reject(self, obj, request):
        """Rejette une demande de congé via le service."""
        notes = request.data.get('approval_notes', '')
        success = LeaveService.reject_leave_request(obj, request.user, notes)

        if success:
            return Response({'message': 'Demande rejetée'})
        return Response({
            'message': 'Impossible de rejeter cette demande'
        }, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Retourne les statistiques des congés."""
        organization = self.get_organization_from_request(raise_exception=False)
        if not organization:
            return Response({'error': 'Organisation requise'}, status=400)

        year = request.query_params.get('year')
        stats = LeaveService.get_organization_leave_stats(
            organization,
            year=int(year) if year else None
        )
        return Response(stats)
```

**Avantages:**
- ✅ Réduit de 60% (~80 lignes vs ~200)
- ✅ Logique métier dans `LeaveService`
- ✅ Comportements réutilisables via mixins
- ✅ Export PDF générique
- ✅ Approve/Reject génériques
- ✅ Plus facile à tester et maintenir

---

### Exemple 3: PayrollPeriodViewSet

#### Après (Pattern complet)

```python
class PayrollPeriodViewSetRefactored(HRViewSetMixin, viewsets.ModelViewSet):
    """
    ViewSet pour la gestion des périodes de paie - VERSION REFACTORÉE.

    Utilise:
    - HRViewSetMixin pour le filtrage par organisation
    - PayrollService pour la logique métier
    """
    queryset = PayrollPeriod.objects.all()
    permission_classes = [IsAdminUserOrEmployee, RequiresPayrollPermission]

    # Configuration du mixin
    view_permission = 'can_view_payroll'
    create_permission = 'can_create_payroll'

    @action(detail=True, methods=['post'])
    def generate_payslips(self, request, pk=None):
        """Génère les fiches de paie pour la période."""
        period = self.get_object()

        # Optionnel: filtrer les employés
        employee_ids = request.data.get('employee_ids', [])
        if employee_ids:
            employees = Employee.objects.filter(
                id__in=employee_ids,
                organization=period.organization,
                is_active=True
            )
        else:
            employees = None

        # Délégation au service
        count = PayrollService.generate_payslips_for_period(period, employees)
        return Response({'message': f'{count} fiches de paie générées'})

    @action(detail=True, methods=['post'])
    def process(self, request, pk=None):
        """Traite la période de paie."""
        period = self.get_object()
        success = PayrollService.process_payroll_period(period)

        if success:
            return Response({'message': 'Période traitée'})
        return Response({
            'message': 'Impossible de traiter cette période'
        }, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def close(self, request, pk=None):
        """Clôture la période de paie."""
        period = self.get_object()
        success = PayrollService.close_payroll_period(period)

        if success:
            return Response({'message': 'Période clôturée'})
        return Response({
            'message': 'Impossible de clôturer cette période'
        }, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Retourne les statistiques de paie."""
        organization = self.get_organization_from_request(raise_exception=False)
        if not organization:
            return Response({'error': 'Organisation requise'}, status=400)

        year = request.query_params.get('year')
        stats = PayrollService.get_organization_payroll_stats(
            organization,
            year=int(year) if year else None
        )
        return Response(stats)
```

**Avantages:**
- ✅ Toutes les opérations complexes dans `PayrollService`
- ✅ ViewSet focalisé sur la présentation
- ✅ Actions réutilisables
- ✅ Facile à tester unitairement

---

## 📊 Comparaison Avant/Après

### Réduction de Code

| ViewSet | Avant | Après | Réduction |
|---------|-------|-------|-----------|
| **EmployeeViewSet** | ~150 lignes | ~50 lignes | **-67%** |
| **LeaveRequestViewSet** | ~200 lignes | ~80 lignes | **-60%** |
| **PayrollPeriodViewSet** | ~120 lignes | ~70 lignes | **-42%** |

### Séparation des Responsabilités

**Avant:**
- ViewSet = Présentation + Logique métier + Requêtes + Permissions
- Tout mélangé dans 150-200 lignes

**Après:**
- ViewSet = Présentation uniquement (50-80 lignes)
- Service = Logique métier
- Mixin = Comportements réutilisables
- Repository = Requêtes (si applicable)

---

## 🎯 Recommandations pour Appliquer ces Patterns

### 1. Commencer par les Services

Extraire la logique métier complexe :

```python
# Dans hr/services.py
class LeaveService:
    @staticmethod
    def create_leave_request(employee, leave_type, start_date, end_date, reason=''):
        """Crée une demande de congé avec toutes les validations."""
        # Toute la logique ici
        pass

    @staticmethod
    def approve_leave_request(leave_request, approver, notes=''):
        """Approuve une demande avec mise à jour du solde."""
        # Toute la logique ici
        pass
```

### 2. Identifier les Patterns Communs

Créer des mixins pour les comportements répétitifs :

```python
# Dans hr/mixins.py
class ApprovableMixin:
    """Mixin pour les objets approvables."""

    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        obj = self.get_object()
        return self._do_approve(obj, request)

    def _do_approve(self, obj, request):
        """À implémenter dans la sous-classe."""
        raise NotImplementedError
```

### 3. Migrer Progressivement

Ne pas tout refactoriser d'un coup :

1. Commencer par 1 ViewSet complexe
2. Créer le service correspondant
3. Tester
4. Passer au suivant

### 4. Tester Chaque Composant

```python
# Test du service (indépendant du ViewSet)
def test_create_leave_request():
    employee = Employee.objects.create(...)
    leave = LeaveService.create_leave_request(
        employee=employee,
        leave_type=leave_type,
        start_date=date(2024, 1, 1),
        end_date=date(2024, 1, 5)
    )
    assert leave.days == 5

# Test du ViewSet (focalisé sur la présentation)
def test_leave_request_viewset_create(api_client):
    response = api_client.post('/api/leave-requests/', {...})
    assert response.status_code == 201
```

---

## 🚀 Prochaines Étapes

### Pour le Module HR

1. **Créer les services manquants**
   - `DepartmentService`
   - `AttendanceService`
   - `ContractService`

2. **Créer des mixins supplémentaires**
   - `StatsMixin` - Pour les endpoints de statistiques
   - `BulkActionMixin` - Pour les actions en masse
   - `HistoryMixin` - Pour l'historique des modifications

3. **Refactoriser les ViewSets existants**
   - Migrer progressivement vers le pattern Service Layer
   - Utiliser les mixins pour réduire la duplication

4. **Tests**
   - Tests unitaires des services
   - Tests d'intégration des ViewSets
   - Coverage minimum: 80%

---

## 📚 Ressources

### Documentation des Patterns

- **Service Layer:** `hr/services.py`
- **Mixins:** `hr/mixins.py`
- **Permissions:** `hr/permissions.py`
- **Repositories:** À créer si nécessaire

### Fichiers de Référence

- ✅ `REFACTORING_PHASE1_SUMMARY.md` - Patterns inventory
- ✅ `REFACTORING_GUIDE.md` - Guide d'utilisation
- ✅ `HR_REFACTORING_PATTERNS.md` - Ce document

---

**Note:** Les exemples de ce document proviennent de `hr/views_refactored.py`, un fichier de démonstration qui a été archivé dans cette documentation.

---

**Généré par:** Claude Code
**Date:** 2025-12-27
**Version:** HR Refactoring Patterns
