from tigaserver_app.models import Photo, IAScore


def create_prediction(photo: Photo) -> IAScore:
    return IAScore.objects.create(
        report=photo.report,
        photo=photo,
        insect_confidence=0.93,
        ae_aegypti=0.8,
        ae_albopictus=0.01,
        anopheles=0.01,
        culex=0.01,
        culiseta=0.01,
        ae_japonicus=0.01,
        ae_koreicus=0.01,
        other_species=0.01,
        not_sure=0,
        x_tl=0,
        x_br=photo.photo.width / 2,
        y_tl=0,
        y_br=photo.photo.height / 2
    )