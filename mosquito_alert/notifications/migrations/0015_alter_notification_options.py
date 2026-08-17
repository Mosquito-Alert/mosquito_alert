from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("notifications", "0014_alter_usersubscription_unique_together_and_more"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="notification",
            options={
                "db_table": "tigaserver_app_notification",
                "permissions": [
                    (
                        "bypass_audience_scope",
                        "Can bypass audience scope",
                    ),
                ],
            },
        ),
    ]
