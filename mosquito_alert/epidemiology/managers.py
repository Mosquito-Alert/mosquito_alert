from django.db.models import Manager


class MonthlyDistributionManager(Manager):
    def get_queryset(self):
        """Sets the custom queryset as the default."""
        return (
            super().get_queryset().exclude(taxon__disease_vector__isnull=True)
        )  # Get only those that are disesases_vectors
