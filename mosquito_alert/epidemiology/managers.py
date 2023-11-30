from mosquito_alert.taxa.managers import SpecieDistributionManager


class DiseaseVectorDistributionManager(SpecieDistributionManager):
    def get_queryset(self):
        """Sets the custom queryset as the default."""
        return (
            super().get_queryset().exclude(taxon__disease_vector__isnull=True)
        )  # Get only those that are disesases_vectors
