# Generated by Django 4.0.8 on 2023-01-19 10:08

from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone
import imagekit.models.fields
import taggit.managers
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('contenttypes', '0002_remove_content_type_name'),
        ('geo', '0001_initial'),
        ('taggit', '0005_auto_20220424_2025'),
    ]

    operations = [
        migrations.CreateModel(
            name='Report',
            fields=[
                ('uuid', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False, unique=True)),
                ('observed_at', models.DateTimeField(blank=True, default=django.utils.timezone.now)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('note', models.TextField(blank=True, null=True)),
                ('location', models.OneToOneField(help_text='The location where the report is created.', on_delete=django.db.models.deletion.PROTECT, related_name='report', to='geo.location')),
                ('polymorphic_ctype', models.ForeignKey(editable=False, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='polymorphic_%(app_label)s.%(class)s_set+', to='contenttypes.contenttype')),
                ('tags', taggit.managers.TaggableManager(blank=True, help_text='A comma-separated list of tags you can add to a report to make them easier to find.', through='taggit.TaggedItem', to='taggit.Tag', verbose_name='Tags')),
            ],
            options={
                'verbose_name': 'report',
                'verbose_name_plural': 'reports',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='BiteReport',
            fields=[
                ('report_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='reports.report')),
            ],
            options={
                'verbose_name': 'bite report',
                'verbose_name_plural': 'bite reports',
            },
            bases=('reports.report',),
        ),
        migrations.CreateModel(
            name='BreedingSiteReport',
            fields=[
                ('report_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='reports.report')),
                ('has_water', models.BooleanField()),
            ],
            options={
                'verbose_name': 'breeding site report',
                'verbose_name_plural': 'breeding site reports',
            },
            bases=('reports.report',),
        ),
        migrations.CreateModel(
            name='IndividualReport',
            fields=[
                ('report_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='reports.report')),
            ],
            options={
                'verbose_name': 'report of an individual',
                'verbose_name_plural': 'individual reports',
            },
            bases=('reports.report',),
        ),
        migrations.CreateModel(
            name='ReportPhoto',
            fields=[
                ('uuid', models.UUIDField(primary_key=True, serialize=False)),
                ('image', imagekit.models.fields.ProcessedImageField(upload_to='photos')),
                ('report', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='photos', to='reports.report')),
            ],
            options={
                'verbose_name': 'photo',
                'verbose_name_plural': 'photos',
            },
        ),
    ]