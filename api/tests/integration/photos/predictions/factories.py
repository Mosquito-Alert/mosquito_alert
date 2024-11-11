from tigaserver_app.models import Photo, PhotoPrediction


def create_photo_prediction(photo: Photo) -> PhotoPrediction:
    return PhotoPrediction.objects.create(
        photo=photo,
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
        x_br=photo.photo.width / 2,
        y_tl=0,
        y_br=photo.photo.height / 2
    )