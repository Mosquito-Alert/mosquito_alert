from mosquito_alert.tigaserver_app.models import Device
from mosquito_alert.users.models import TigaUser

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
