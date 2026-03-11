from django.db import models
import uuid
from django.utils import timezone


class TimeStampedModel(models.Model):
    """Modèle abstrait avec timestamps et soft delete"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        abstract = True

    def soft_delete(self):
        self.deleted_at = timezone.now()
        self.save()

    def restore(self):
        self.deleted_at = None
        self.save()


# Import pour rétrocompatibilité - BaseUser et BaseProfile sont maintenant dans core
def _get_base_user():
    """Import lazy pour éviter les imports circulaires"""
    from core.models import BaseUser
    return BaseUser

# Ces alias seront résolus au premier accès
# Pour la rétrocompatibilité, utilisez directement: from core.models import BaseUser
