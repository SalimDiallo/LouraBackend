"""
Custom pagination classes for the API

Classes:
- StandardResultsSetPagination: Default (10/page, max 100) — pour la majorité des vues
- SmallResultsSetPagination: Compact (5/page, max 50) — pour les widgets/dropdowns paginés
- LargeResultsSetPagination: Large (50/page, max 100) — pour les exports/rapports
- NoPagination: Pas de pagination — pour les lookups complets (warehouses, categories, etc.)
"""
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response


class StandardResultsSetPagination(PageNumberPagination):
    """
    Pagination standard — 10 éléments par page.

    Format de réponse:
    {
        "count": total_count,
        "next": next_page_url | null,
        "previous": previous_page_url | null,
        "results": [...]
    }

    Paramètres query supportés:
    - page: numéro de page (défaut: 1)
    - page_size: taille de page (défaut: 10, max: 100)
    """
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100

    def get_paginated_response(self, data):
        return Response({
            'count': self.page.paginator.count,
            'next': self.get_next_link(),
            'previous': self.get_previous_link(),
            'results': data
        })


class SmallResultsSetPagination(PageNumberPagination):
    """
    Pagination compacte — 5 éléments par page.
    Pour les widgets, sidebars et listes compactes.
    """
    page_size = 5
    page_size_query_param = 'page_size'
    max_page_size = 50

    def get_paginated_response(self, data):
        return Response({
            'count': self.page.paginator.count,
            'next': self.get_next_link(),
            'previous': self.get_previous_link(),
            'results': data
        })


class LargeResultsSetPagination(PageNumberPagination):
    """
    Pagination large — 50 éléments par page.
    Pour les exports, rapports et listes volumineuses.
    """
    page_size = 50
    page_size_query_param = 'page_size'
    max_page_size = 100

    def get_paginated_response(self, data):
        return Response({
            'count': self.page.paginator.count,
            'next': self.get_next_link(),
            'previous': self.get_previous_link(),
            'results': data
        })

