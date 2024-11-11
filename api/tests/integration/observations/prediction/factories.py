from tigaserver_app.models import PhotoPrediction, ObservationPrediction

def create_observation_prediction(photo_prediction: PhotoPrediction) -> ObservationPrediction:
    return ObservationPrediction.objects.create(
        report=photo_prediction.photo.report,
        photo_prediction=photo_prediction
    )