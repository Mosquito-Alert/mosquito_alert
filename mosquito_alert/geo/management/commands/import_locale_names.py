import argparse
import logging
import sys
from operator import itemgetter

import tablib
from django.core.management.base import BaseCommand
from django.db import transaction
from modeltranslation.translator import translator
from tqdm import tqdm

from ...import_export.data_sources import NAME_SOURCES
from ...import_export.data_sources.base import OnlineDataSource
from ...import_export.resources import BoundaryResource
from ...models import Boundary


class ReverseCandidatesException(Exception):
    pass


class TooManyCandidatesException(ReverseCandidatesException):
    pass


class NoCandidatesExceptions(ReverseCandidatesException):
    pass


class Command(BaseCommand):
    help = "Import boundaries data."

    def add_arguments(self, parser):

        parser.add_argument(
            "--bl_pk",
            type=int,
            required=True,
            help="Assign a boundary layer already found in the DB.",
        )

        parser.add_argument(
            "--filter_name_by",
            type=str,
            required=False,
            help="Filter boundaries by its name.",
        )

        parser.add_argument(
            "--dry-run",
            dest="dry_run",
            action="store_true",
            help="Execute in dry-run mode.",
        )

        subparser = parser.add_subparsers(title="source", dest="source", required=True)

        for s in NAME_SOURCES:
            s_parser = subparser.add_parser(
                s.CLI_NAME, formatter_class=argparse.ArgumentDefaultsHelpFormatter
            )
            s_parser.set_defaults(**{subparser.dest: s})
            s.add_arguments(s_parser)

    def get_translation(self, data_source, boundary, location_type, language):
        locations = data_source.reverse(
            geometry=boundary.geometry,
            location_type=location_type,
            language_iso=language,
            exactly_one=False,
        )

        if not locations:
            raise ReverseCandidatesException(
                f"No naming candidate found for boundary {boundary} (pk: {boundary.pk})"
            )
        if len(locations) > 1:
            raise ReverseCandidatesException(
                "Multiple location candidates found for boundary {} (pk: {}) -> {}. "
                "Please edit it manually. Skipping...".format(
                    boundary, boundary.pk, [x.name for x in locations]
                )
            )

        return locations[0].name

    def get_all_translations(self, data_source, boundary, location_type, languages):
        result = dict.fromkeys(languages)
        for lang in languages:
            try:
                resul_transl = self.get_translation(
                    data_source=data_source,
                    boundary=boundary,
                    location_type=location_type,
                    language=lang,
                )
            except ReverseCandidatesException as e:
                logging.warn(e)
                return result
            else:
                result[lang] = resul_transl

        return result

    def create_dataset(self, boundary_qs, data_source, location_type):
        logging.info("Creating dataset.")

        _name_field = "name"
        trans_opts = translator.get_options_for_model(Boundary)
        if _name_field not in trans_opts.fields:
            raise ValueError(
                f"Field {_name_field} has no translation candidates {trans_opts}."
            )

        trans_field = trans_opts.fields.get(_name_field)

        dataset = tablib.Dataset(headers=["id"] + [x.name for x in trans_field])

        for b in (p_bar := tqdm(boundary_qs.prefetch_geometry().all())):
            # Update probress bar description
            p_bar.set_description(f"{b.name} (pk: {b.pk})")

            # Start building the result list that will be appended to dataset.
            result = [
                b.pk,
            ]
            result_translations = self.get_all_translations(
                data_source=data_source,
                boundary=b,
                location_type=location_type,
                languages=[x.language for x in trans_field],
            )
            if not any(result_translations.values()):
                # Case all values are None
                continue

            # Merge translations results in the same order than the headers.
            result = result + list(
                itemgetter(*map(lambda x: x.language, trans_field))(result_translations)
            )

            dataset.append(result)

        return dataset

    @transaction.atomic
    def handle(self, *args, **options):

        self.set_logging(verbosity=int(options["verbosity"]))

        sp = transaction.savepoint()
        logging.debug("Saved transaction savepoint.")

        naming_source_cls = options.get("source")

        if issubclass(naming_source_cls, OnlineDataSource):
            naming_source = naming_source_cls.from_online_source(**options)
        else:
            naming_source = naming_source_cls(**options)

        boundary_filters = {"boundary_layer__pk": options.get("bl_pk")}
        if options.get("filter_name_by"):
            boundary_filters["name__icontains"] = options.get("filter_name_by")

        dataset = self.create_dataset(
            boundary_qs=Boundary.objects.filter(**boundary_filters),
            data_source=naming_source,
            location_type=options.get(
                "location_type"
            ),  # See import_export.data_sources.names.BaseBoundaryNameDataSource
        )

        logging.info("Importing translations.")
        result = BoundaryResource(show_progess_bar=True).import_data(
            dataset,
            dry_run=options.get("dry_run"),
            raise_errors=True,
            use_transactions=True,
            collect_failed_rows=True,
            rollback_on_validation_errors=False,
        )

        if result.has_errors():
            for _, err in result.row_errors():
                for current_err in err:
                    logging.error(current_err.error, current_err.traceback)

        if options.get("dry_run") or result.has_errors():
            logging.warning("Start rollback.")
            transaction.savepoint_rollback(sid=sp)
            logging.debug("Rollback finished.")
        else:
            logging.debug("Saving commit (transaction atomic)")
            transaction.savepoint_commit(sid=sp)

    def set_logging(self, verbosity):
        if verbosity == 0:
            logging.getLogger(sys.argv[0]).setLevel(logging.WARN)
        elif verbosity == 1:  # default
            logging.getLogger(sys.argv[0]).setLevel(logging.INFO)
        elif verbosity > 1:
            logging.getLogger(sys.argv[0]).setLevel(logging.DEBUG)
        if verbosity > 2:
            logging.getLogger().setLevel(logging.DEBUG)
