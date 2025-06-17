from tigacrafting.models import PhotoPrediction, Taxon
from tigaserver_app.models import Photo


def create_photo_prediction(photo: Photo) -> PhotoPrediction:
    # Needs to be sure that exists a taxon for the predicted_class
    predicted_class = PhotoPrediction.CLASS_FIELDNAMES_CHOICES[0][0]

    try:
        Taxon.objects.get(pk=PhotoPrediction.PREDICTED_CLASS_TO_TAXON[predicted_class])
    except Taxon.DoesNotExist:
        taxon_root = Taxon.get_root() or Taxon.add_root(
            rank=Taxon.TaxonomicRank.CLASS,
            name="Insecta",
            common_name=""
        )
        taxon_root.add_child(
            pk=PhotoPrediction.PREDICTED_CLASS_TO_TAXON[predicted_class],
            rank=Taxon.TaxonomicRank.SPECIES,
            name=PhotoPrediction.CLASS_FIELDNAMES_CHOICES[0][1],
            is_relevant=True
        )

    return PhotoPrediction.objects.create(
        photo=photo,
        identification_task=photo.report.identification_task,
        classifier_version=PhotoPrediction.CLASSIFIER_VERSION_CHOICES[0][0],
        insect_confidence=0.93,
        predicted_class=PhotoPrediction.CLASS_FIELDNAMES_CHOICES[0][0],
        threshold_deviation=0.9,
        ae_aegypti_score=0.8,
        ae_albopictus_score=0.01,
        anopheles_score=0.01,
        culex_score=0.01,
        culiseta_score=0.01,
        ae_japonicus_score=0.01,
        ae_koreicus_score=0.01,
        other_species_score=0.01,
        not_sure_score=0,
        x_tl=0,
        x_br=0.5,
        y_tl=0,
        y_br=0.5
    )