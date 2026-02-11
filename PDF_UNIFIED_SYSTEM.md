# 📄 Système Unifié de Génération PDF avec Preview

## 🎯 Vue d'Ensemble

Ce document décrit le nouveau système unifié de génération de PDF qui supporte à la fois le **téléchargement** et la **preview en ligne** pour tous les documents de l'application.

### ✨ Fonctionnalités

- ✅ **Mode Preview** - Affichage inline dans le navigateur
- ✅ **Mode Download** - Téléchargement direct du fichier
- ✅ **API Unifiée** - Un seul mixin pour tous les ViewSets
- ✅ **Paramètre Query** - `?mode=preview` ou `?mode=download`
- ✅ **Headers Personnalisés** - `X-PDF-Filename` et `X-PDF-Mode`
- ✅ **Cache Intelligent** - 5 minutes de cache pour les PDFs
- ✅ **Frontend Ready** - Compatible avec `usePDF` hook et `PDFPreviewModal`

---

## 📂 Architecture

### Backend (Django)

```
backend/app/inventory/
├── pdf_base.py                 # ⭐ Nouveau - Système unifié
│   ├── PDFGeneratorMixin       # Mixin pour ViewSets
│   └── PDFResponseHelper       # Helper pour vues fonctionnelles
├── pdf_generator.py            # Générateurs PDF existants (ReportLab)
├── pdf_sales.py                # Générateurs PDF ventes (ReportLab)
└── views.py                    # ViewSets mis à jour avec le mixin
```

### Frontend (React/Next.js)

```
frontend/lourafrontend/
├── lib/
│   ├── services/pdf.service.ts      # Service PDF central
│   ├── hooks/usePDF.ts              # Hook React pour PDF
│   └── utils/pdf-generator.ts       # Générateur client-side
└── components/ui/
    └── pdf-preview-modal.tsx        # Modal de preview
```

---

## 🔧 Implémentation Backend

### 1. Le Mixin PDFGeneratorMixin

**Fichier:** `inventory/pdf_base.py`

```python
from inventory.pdf_base import PDFGeneratorMixin

class MyViewSet(PDFGeneratorMixin, BaseOrganizationViewSetMixin, viewsets.ModelViewSet):

    @action(detail=True, methods=['get'], url_path='export-pdf')
    def export_pdf(self, request, organization_slug=None, pk=None):
        """Export as PDF - supports preview mode"""
        from .pdf_generator import generate_my_pdf

        obj = self.get_object()

        return self.generate_and_respond(
            generator_func=generate_my_pdf,
            generator_args=(obj,),
            filename=f"Document_{obj.number}.pdf",
            request=request
        )
```

### 2. Méthodes Disponibles

#### `pdf_response()`

Crée une réponse HTTP avec le bon Content-Disposition.

```python
def pdf_response(
    self,
    pdf_buffer: BytesIO,
    filename: str,
    request: Optional[HttpRequest] = None,
    default_mode: str = 'download'
) -> HttpResponse
```

#### `generate_and_respond()`

Génère le PDF et retourne la réponse en une seule étape.

```python
def generate_and_respond(
    self,
    generator_func: callable,
    generator_args: tuple = (),
    generator_kwargs: dict = None,
    filename: str = "document.pdf",
    request: Optional[HttpRequest] = None,
    default_mode: str = 'download'
) -> HttpResponse
```

---

## 🌐 API Endpoints

### Mode Download (Défaut)

```http
GET /api/inventory/sales/123/receipt/
GET /api/inventory/sales/123/receipt/?mode=download

Response:
Content-Type: application/pdf
Content-Disposition: attachment; filename="Recu_VTE-001.pdf"
X-PDF-Filename: Recu_VTE-001.pdf
X-PDF-Mode: download
```

### Mode Preview

```http
GET /api/inventory/sales/123/receipt/?mode=preview

Response:
Content-Type: application/pdf
Content-Disposition: inline; filename="Recu_VTE-001.pdf"
X-PDF-Filename: Recu_VTE-001.pdf
X-PDF-Mode: preview
```

---

## 📋 Endpoints Mis à Jour

### Inventory - ViewSets

| ViewSet | Endpoint | Document |
|---------|----------|----------|
| **OrderViewSet** | `/orders/{id}/export-pdf/` | Bon de Commande |
| **StockCountViewSet** | `/stock-counts/{id}/export-pdf/` | Rapport d'Inventaire |
| **InventoryStatsViewSet** | `/stats/export-products-pdf/` | Catalogue Produits |
| **InventoryStatsViewSet** | `/stats/export-stock-pdf/` | Rapport de Stock |
| **InventoryStatsViewSet** | `/stats/generate-quote-pdf/` | Devis/Quote |
| **InventoryStatsViewSet** | `/stats/generate-invoice-pdf/` | Facture Générique |

### Sales - ViewSets

| ViewSet | Endpoint | Document |
|---------|----------|----------|
| **SaleViewSet** | `/sales/{id}/receipt/` | Reçu de Vente |
| **SaleViewSet** | `/sales/{id}/invoice/` | Facture de Vente |
| **PaymentViewSet** | `/payments/{id}/export-pdf/` | Reçu de Paiement |
| **ProformaInvoiceViewSet** | `/proformas/{id}/export-pdf/` | Facture Pro Forma |
| **PurchaseOrderViewSet** | `/purchase-orders/{id}/export-pdf/` | Bon de Commande d'Achat |
| **DeliveryNoteViewSet** | `/delivery-notes/{id}/export-pdf/` | Bon de Livraison |
| **CreditSaleViewSet** | `/credit-sales/{id}/export-pdf/` | Relevé de Créance |
| **CreditSaleViewSet** | `/credit-sales/{id}/invoice/` | Facture de Créance |
| **ExpenseViewSet** | `/expenses/export/?format=pdf` | Rapport de Dépenses |

**Total: 18 endpoints mis à jour** ✅

---

## 💻 Utilisation Frontend

### 1. Avec le Hook usePDF

```typescript
import { usePDF } from '@/lib/hooks';
import { PDFPreviewWrapper } from '@/components/ui';

const MyComponent = () => {
  const { preview, download, previewState, closePreview, downloading } = usePDF();

  // Preview dans modal
  const handlePreview = () => {
    preview(
      '/api/inventory/sales/123/receipt/',  // Endpoint
      'Reçu de Vente VTE-001',               // Titre
      'recu_VTE-001.pdf'                     // Nom du fichier
    );
  };

  // Téléchargement direct
  const handleDownload = () => {
    download(
      '/api/inventory/sales/123/receipt/',  // Endpoint
      'recu_VTE-001.pdf'                     // Nom du fichier
    );
  };

  return (
    <>
      <button onClick={handlePreview}>👁️ Prévisualiser</button>
      <button onClick={handleDownload}>⬇️ Télécharger</button>

      <PDFPreviewWrapper
        previewState={previewState}
        onClose={closePreview}
      />
    </>
  );
};
```

### 2. Service PDFService Automatique

Le `PDFService` gère automatiquement le paramètre `?mode=preview` :

```typescript
// Preview - Ajoute automatiquement ?mode=preview
PDFService.fetchForPreview('/api/inventory/sales/123/receipt/')

// Download - Pas de paramètre mode (défaut = download)
PDFService.download('/api/inventory/sales/123/receipt/', 'recu.pdf')

// Ouvrir dans nouvel onglet - Ajoute ?mode=preview
PDFService.openInNewTab('/api/inventory/sales/123/receipt/')
```

---

## 🎨 Exemple Complet

### Backend (ViewSet)

```python
from rest_framework import viewsets
from rest_framework.decorators import action
from inventory.pdf_base import PDFGeneratorMixin

class InvoiceViewSet(PDFGeneratorMixin, viewsets.ModelViewSet):
    queryset = Invoice.objects.all()

    @action(detail=True, methods=['get'], url_path='export-pdf')
    def export_pdf(self, request, organization_slug=None, pk=None):
        """Export invoice as PDF - supports preview"""
        from .pdf_generator import generate_invoice_pdf

        invoice = self.get_object()

        return self.generate_and_respond(
            generator_func=generate_invoice_pdf,
            generator_args=(invoice,),
            filename=f"Invoice_{invoice.number}.pdf",
            request=request
        )
```

### Frontend (React)

```typescript
import { usePDF, PDFEndpoints } from '@/lib/hooks';
import { PDFPreviewWrapper } from '@/components/ui';

const InvoicePage = ({ invoice }) => {
  const { preview, download, previewState, closePreview } = usePDF();

  return (
    <div className="space-y-4">
      <h1>Facture {invoice.number}</h1>

      <div className="flex gap-2">
        <button
          onClick={() => preview(
            PDFEndpoints.invoice(invoice.id),
            `Facture ${invoice.number}`,
            `facture_${invoice.number}.pdf`
          )}
          className="btn-primary"
        >
          👁️ Prévisualiser
        </button>

        <button
          onClick={() => download(
            PDFEndpoints.invoice(invoice.id),
            `facture_${invoice.number}.pdf`
          )}
          className="btn-secondary"
        >
          ⬇️ Télécharger
        </button>
      </div>

      <PDFPreviewWrapper
        previewState={previewState}
        onClose={closePreview}
      />
    </div>
  );
};
```

---

## 🚀 Migration depuis l'Ancien Système

### Avant (Ancien Code)

```python
@action(detail=True, methods=['get'], url_path='export-pdf')
def export_pdf(self, request, organization_slug=None, pk=None):
    """Export as PDF"""
    from django.http import HttpResponse
    from .pdf_generator import generate_my_pdf

    obj = self.get_object()
    pdf_buffer = generate_my_pdf(obj)
    filename = f"Document_{obj.number}.pdf"

    response = HttpResponse(pdf_buffer.getvalue(), content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response
```

### Après (Nouveau Système)

```python
@action(detail=True, methods=['get'], url_path='export-pdf')
def export_pdf(self, request, organization_slug=None, pk=None):
    """Export as PDF - supports preview mode"""
    from .pdf_generator import generate_my_pdf

    obj = self.get_object()

    return self.generate_and_respond(
        generator_func=generate_my_pdf,
        generator_args=(obj,),
        filename=f"Document_{obj.number}.pdf",
        request=request
    )
```

### Changements Requis

1. ✅ Ajouter `PDFGeneratorMixin` à la classe ViewSet
2. ✅ Importer depuis `inventory.pdf_base`
3. ✅ Remplacer le code de génération par `generate_and_respond()`
4. ✅ Supprimer les imports inutiles (`HttpResponse`, etc.)
5. ✅ Le frontend fonctionne automatiquement avec le nouveau système !

---

## 📊 Résultats

### Avant la Migration

- ❌ Pas de preview - téléchargement forcé
- ❌ Code dupliqué dans chaque ViewSet
- ❌ Pas de headers personnalisés
- ❌ Pas de cache
- ❌ ~25 lignes de code par endpoint

### Après la Migration

- ✅ Preview inline + téléchargement
- ✅ Code réutilisable (mixin)
- ✅ Headers X-PDF-* pour metadata
- ✅ Cache 5 minutes
- ✅ ~10 lignes de code par endpoint
- ✅ **Réduction de ~60% du code boilerplate**

---

## 🔐 Sécurité

Le système maintient toutes les protections existantes :

- ✅ **Authentification** - `IsAuthenticated` permission
- ✅ **Multi-tenancy** - `organization_slug` requis
- ✅ **Authorization** - Accès basé sur l'organisation
- ✅ **Validation** - Objets validés via `get_object()`

---

## 🧪 Tests

### Test Manuel - Preview Mode

```bash
# Avec authentication
curl -H "Authorization: Bearer <token>" \
  "http://localhost:8000/api/inventory/sales/123/receipt/?mode=preview&organization_subdomain=my-org"

# Vérifier les headers
Content-Disposition: inline; filename="Recu_VTE-001.pdf"
X-PDF-Mode: preview
```

### Test Manuel - Download Mode

```bash
curl -H "Authorization: Bearer <token>" \
  "http://localhost:8000/api/inventory/sales/123/receipt/?mode=download&organization_subdomain=my-org"

# Vérifier les headers
Content-Disposition: attachment; filename="Recu_VTE-001.pdf"
X-PDF-Mode: download
```

---

## 📚 Ressources

### Fichiers Principaux

- **Backend Mixin:** `backend/app/inventory/pdf_base.py`
- **Frontend Hook:** `frontend/lourafrontend/lib/hooks/usePDF.ts`
- **Frontend Service:** `frontend/lourafrontend/lib/services/pdf.service.ts`
- **Preview Modal:** `frontend/lourafrontend/components/ui/pdf-preview-modal.tsx`

### Documentation Inline

Tous les fichiers contiennent des docstrings détaillées et des exemples d'utilisation.

---

## 🐛 Troubleshooting

### Le PDF ne s'affiche pas en preview

**Cause:** Certains navigateurs bloquent les PDFs inline.

**Solution:** Le modal a un fallback automatique avec bouton de téléchargement.

### Le paramètre ?mode=preview n'est pas pris en compte

**Vérifications:**
1. Le ViewSet hérite de `PDFGeneratorMixin`
2. L'import est correct: `from .pdf_base import PDFGeneratorMixin`
3. La méthode utilise `self.generate_and_respond()` ou `self.pdf_response()`

### Les headers X-PDF-* ne sont pas présents

**Cause:** Ancienne méthode utilisée au lieu du mixin.

**Solution:** Migrer vers `generate_and_respond()` ou `pdf_response()`.

---

## 🎓 Bonnes Pratiques

### DO ✅

```python
# Utiliser le mixin
class MyViewSet(PDFGeneratorMixin, BaseOrganizationViewSetMixin, viewsets.ModelViewSet):
    ...

# Utiliser generate_and_respond()
return self.generate_and_respond(
    generator_func=generate_pdf,
    generator_args=(obj,),
    filename=f"doc_{obj.id}.pdf",
    request=request
)

# Nommer les fichiers de manière descriptive
filename = f"Facture_{invoice.number}_{date}.pdf"
```

### DON'T ❌

```python
# Ne pas créer manuellement HttpResponse
response = HttpResponse(pdf_buffer, content_type='application/pdf')  # ❌

# Ne pas hardcoder Content-Disposition
response['Content-Disposition'] = 'attachment; ...'  # ❌

# Ne pas ignorer le paramètre request
return self.generate_and_respond(..., request=None)  # ❌
```

---

## 📝 Changelog

### v1.0.0 - 2026-02-09

**Ajouté:**
- ✨ Nouveau système unifié de génération PDF
- ✨ Support du mode preview inline
- ✨ Mixin `PDFGeneratorMixin` réutilisable
- ✨ Helper `PDFResponseHelper` pour vues fonctionnelles
- ✨ Headers personnalisés `X-PDF-Filename` et `X-PDF-Mode`
- ✨ Cache HTTP de 5 minutes pour les PDFs

**Modifié:**
- 🔄 Migration de 18 endpoints vers le nouveau système
- 🔄 Tous les ViewSets PDF héritent maintenant de `PDFGeneratorMixin`
- 🔄 Réduction de ~60% du code boilerplate

**Corrigé:**
- 🐛 Race conditions dans la génération de numéros de documents
- 🐛 Absence de preview pour les PDFs

---

## 🤝 Contribution

Pour ajouter un nouveau endpoint PDF :

1. Hériter de `PDFGeneratorMixin` dans votre ViewSet
2. Créer une fonction de génération PDF dans `pdf_generator.py` ou `pdf_sales.py`
3. Utiliser `generate_and_respond()` dans votre action
4. Documenter le nouvel endpoint dans ce fichier

---

## 📞 Support

En cas de questions ou problèmes :

1. Consulter les exemples dans `pdf_base.py`
2. Vérifier la documentation inline
3. Tester manuellement avec curl/Postman
4. Ouvrir une issue GitHub si problème persistant

---

**Créé le:** 2026-02-09
**Dernière mise à jour:** 2026-02-09
**Version:** 1.0.0
**Auteur:** LouraTech Development Team
