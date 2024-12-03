from tigaserver_app.models import Device, TigaUser

def create_device(user: TigaUser) -> Device:
    return Device.objects.create(
        device_id='unique_id',
        registration_id='fcm_token',
        user=user,
        type='android',
        model='test_model',
        os_name='android',
        os_version='32'
    )
