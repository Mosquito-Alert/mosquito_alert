# Generated by Django 4.0.8 on 2023-03-01 13:06

from django.conf import settings
import django.core.validators
from django.db import migrations, models
import django.db.models.deletion
import django_lifecycle.mixins
import mosquito_alert.identifications.mixins


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('images', '0001_initial'),
        ('users', '0001_initial'),
        ('individuals', '0001_initial'),
        ('taxa', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='IdentifierUserProfile',
            fields=[
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, primary_key=True, serialize=False, to=settings.AUTH_USER_MODEL)),
                ('is_superexpert', models.BooleanField(default=False)),
            ],
            options={
                'verbose_name': 'identifier user profile',
                'verbose_name_plural': 'identifier user profiles',
            },
        ),
        migrations.CreateModel(
            name='UserIdentificationSuggestion',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('probability', models.FloatField(choices=[(1.0, "I'm sure"), (0.75, "I'm doubting.")], validators=[django.core.validators.MinValueValidator(0), django.core.validators.MaxValueValidator(1)])),
                ('notes', models.TextField(blank=True, null=True)),
                ('individual', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='individuals.individual')),
                ('taxon', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='taxa.taxon')),
                ('user_profile', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='identifications', to='identifications.identifieruserprofile')),
            ],
            options={
                'verbose_name': 'user identification suggestion',
                'verbose_name_plural': 'user identification suggestions',
            },
            bases=(mosquito_alert.identifications.mixins.MultipleIndividualIdentificationCandidateMixin, django_lifecycle.mixins.LifecycleModelMixin, mosquito_alert.identifications.mixins.ProbabilityTreeModelMixin, models.Model),
        ),
        migrations.CreateModel(
            name='ImageTaxonPredictionRun',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('photo', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='taxon_prediction_run', to='images.photo')),
            ],
            options={
                'verbose_name': 'taxon image prediction run',
                'verbose_name_plural': 'taxon image predictions runs',
            },
        ),
        migrations.CreateModel(
            name='ImageTaxonPrediction',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('probability', models.FloatField(validators=[django.core.validators.MinValueValidator(0), django.core.validators.MaxValueValidator(1)])),
                ('prediction_run', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='image_taxon_predictions', to='identifications.imagetaxonpredictionrun')),
                ('taxon', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='taxa.taxon')),
            ],
            options={
                'verbose_name': 'taxon image prediction',
                'verbose_name_plural': 'taxon image prediction',
                'ordering': ['prediction_run', '-probability'],
            },
            bases=(mosquito_alert.identifications.mixins.ProbabilityTreeModelMixin, models.Model),
        ),
        migrations.CreateModel(
            name='IdentificationResult',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('probability', models.FloatField(validators=[django.core.validators.MinValueValidator(0), django.core.validators.MaxValueValidator(1)])),
                ('type', models.CharField(choices=[('com', 'Community'), ('ens', 'Ensembled')], max_length=3)),
                ('individual', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='individuals.individual')),
                ('taxon', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='taxa.taxon')),
            ],
            options={
                'verbose_name': 'identification result',
                'verbose_name_plural': 'identification results',
                'default_related_name': 'identification_results',
            },
            bases=(mosquito_alert.identifications.mixins.MultipleIndividualIdentificationCandidateMixin, mosquito_alert.identifications.mixins.ProbabilityTreeModelMixin, models.Model),
        ),
        migrations.CreateModel(
            name='ComputerVisionIdentificationSuggestion',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('probability', models.FloatField(validators=[django.core.validators.MinValueValidator(0), django.core.validators.MaxValueValidator(1)])),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('individual', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='individuals.individual')),
                ('taxon', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='taxa.taxon')),
            ],
            options={
                'verbose_name': 'computer vision identification suggestion',
                'verbose_name_plural': 'computer vision identification suggestions',
            },
            bases=(mosquito_alert.identifications.mixins.MultipleIndividualIdentificationCandidateMixin, django_lifecycle.mixins.LifecycleModelMixin, mosquito_alert.identifications.mixins.ProbabilityTreeModelMixin, models.Model),
        ),
        migrations.CreateModel(
            name='CommunityIdentificationResult',
            fields=[
            ],
            options={
                'verbose_name': 'community identification result',
                'verbose_name_plural': 'community identification results',
                'proxy': True,
                'indexes': [],
                'constraints': [],
            },
            bases=(mosquito_alert.identifications.mixins.IdentificationResultProxyMixin, 'identifications.identificationresult'),
        ),
        migrations.CreateModel(
            name='EnsembledIdentificationResult',
            fields=[
            ],
            options={
                'verbose_name': 'ensembled identification result',
                'verbose_name_plural': 'ensembled identification results',
                'proxy': True,
                'indexes': [],
                'constraints': [],
            },
            bases=(mosquito_alert.identifications.mixins.IdentificationResultProxyMixin, 'identifications.identificationresult'),
        ),
        migrations.AddConstraint(
            model_name='useridentificationsuggestion',
            constraint=models.UniqueConstraint(fields=('user_profile', 'individual'), name='unique_user_individual'),
        ),
        migrations.AddConstraint(
            model_name='imagetaxonprediction',
            constraint=models.UniqueConstraint(fields=('taxon', 'prediction_run'), name='unique_taxon_prediction_run'),
        ),
        migrations.AddConstraint(
            model_name='identificationresult',
            constraint=models.UniqueConstraint(fields=('individual', 'type', 'taxon'), name='unique_taxon_individual_type'),
        ),
    ]