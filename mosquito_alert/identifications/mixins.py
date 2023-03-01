from abc import abstractmethod

from .managers import ProxyIdentificationResultManager
from .prob_tree import create_tree_from_identifications


class ProbabilityTreeModelMixin:
    @classmethod
    def get_probability_for_taxon(cls, qs, taxon):
        result = 0

        taxon_in_qs = qs.filter(taxon=taxon)
        if taxon_in_qs.exists():
            result = taxon_in_qs.first().probability
        elif node := cls.get_probability_tree(qs=qs).find_by_taxon(taxon=taxon):
            result = node.probability

        return result

    @classmethod
    def get_probability_tree(cls, qs):
        return create_tree_from_identifications(
            [(obj.taxon, obj.probability) for obj in qs]
        )

    class Meta:
        abstract = True


class MultipleIdentificationCandidateMixin(ProbabilityTreeModelMixin):
    @property
    @abstractmethod
    def grouped_by_fields(self):
        return NotImplementedError

    @classmethod
    def _build_grouped_qs(cls, **kwargs):
        if not set(cls.grouped_by_fields).issubset(set(kwargs.keys())):
            raise ValueError(
                "Missing required fields to build grouped queryset. "
                f"Passed as arguments: {kwargs}, required are {cls.grouped_by_fields}"
            )

        return cls.objects.filter(
            **{key: kwargs.get(key) for key in cls.grouped_by_fields}
        )

    @classmethod
    def get_probability_for_taxon(cls, taxon, **kwargs):
        return super().get_probability_for_taxon(
            qs=cls._build_grouped_qs(**kwargs), taxon=taxon
        )

    @classmethod
    def get_probability_tree(cls, qs=None, **kwargs):
        return super().get_probability_tree(qs=qs or cls._build_grouped_qs(**kwargs))

    @classmethod
    def _update_from_tree(cls, tree, **kwargs):
        tree_nodes = [tree.root] + list(tree.root.descendants)

        qs = cls._build_grouped_qs(**kwargs)

        # Delete objects that does not exist in the tree but exist in the DB.
        qs.exclude(taxon__pk__in=[x.taxon.pk for x in tree_nodes]).delete()

        for node in tree_nodes:
            cls.objects.update_or_create(
                **kwargs,
                taxon=node.taxon,
                defaults={"probability": node.probability},
            )

    class Meta:
        abstract = True


class MultipleIndividualIdentificationCandidateMixin(
    MultipleIdentificationCandidateMixin
):
    # Group by 'individual' field.
    grouped_by_fields = [
        "individual",
    ]

    class Meta:
        abstract = True


class IdentificationResultProxyMixin:

    RESULT_TYPE = None  # Value of IdentificationResultType

    @classmethod
    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        cls.add_to_class(
            "objects", ProxyIdentificationResultManager(type=cls.RESULT_TYPE)
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        setattr(self, "type", self.RESULT_TYPE)

    @classmethod
    def get_probability_tree(cls, individual):
        return super().get_probability_tree(individual=individual, type=cls.RESULT_TYPE)

    @classmethod
    def get_probability_for_taxon(cls, taxon, individual):

        return super().get_probability_for_taxon(
            taxon=taxon, individual=individual, type=cls.RESULT_TYPE
        )

    @classmethod
    def update(cls, individual):
        return super().update(individual=individual, type=cls.RESULT_TYPE)
