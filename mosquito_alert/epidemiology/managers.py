from django.db.models import Manager


class MonthlyDistributionManager(Manager):
    def get_queryset(self):
        """Sets the custom queryset as the default."""
        return (
            super().get_queryset().select_related("taxa__disease_vector")
        )  # Get only those that are disesases_vectors
