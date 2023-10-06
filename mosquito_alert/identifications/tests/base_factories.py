from factory.django import DjangoModelFactory

##########################
# Identifier Profile
##########################


class BaseIdentifierProfileFactory(DjangoModelFactory):
    class Meta:
        abstract = True
