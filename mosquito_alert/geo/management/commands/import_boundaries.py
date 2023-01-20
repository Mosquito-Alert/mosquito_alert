import argparse
import logging
import sys
from operator import itemgetter

from django.core.management.base import BaseCommand
from django.db import transaction

from ...import_export.data_sources import BOUNDARY_SOURCES
from ...import_export.data_sources.base import OnlineDataSource
from ...import_export.formats import ZippedShapefileFormat
from ...import_export.resources import BoundaryResource
from ...models import Boundary, BoundaryLayer


class Command(BaseCommand):
    help = "Import boundaries data."

    def add_arguments(self, parser):

        boundary_layer_group = parser.add_argument_group("Boundary layer")
        boundary_layer_group.add_argument(
            "--bl_pk", type=int, help="Assign a boundary layer already found in the DB."
        )
        boundary_layer_group.add_argument(
            "--bl_type",
            type=str,
            choices=BoundaryLayer.BoundaryType.values,
            help="Assign a boundary layer type.",
        )
        boundary_layer_group.add_argument(
            "--bl_level", type=int, help="Assign a boundary layer level."
        )
        boundary_layer_group.add_argument(
            "--bl_boundary_pk",
            type=int,
            help="Assign a boundary to this boundary layer.",
        )

        boundary_layer_group.add_argument(
            "--bl_parent_pk",
            type=int,
            required=False,
            help="Parent boundary layer to use to generate relations between "
            "current geometries and their relative parents.",
        )

        parser.add_argument(
            "--file_path",
            dest="uri",
            required=False,
            help="Path to a GDAL-supported file.",
        )

        parser.add_argument(
            "--dry-run",
            dest="dry_run",
            action="store_true",
            help="Execute in dry-run mode.",
        )

        subparser = parser.add_subparsers(title="source", dest="source", required=True)

        for s in BOUNDARY_SOURCES:
            s_parser = subparser.add_parser(
                s.CLI_NAME, formatter_class=argparse.ArgumentDefaultsHelpFormatter
            )
            s_parser.set_defaults(**{subparser.dest: s})
            s.add_arguments(s_parser)

    @transaction.atomic
    def handle(self, *args, **options):
        self.set_logging(verbosity=int(options["verbosity"]))

        if not options.get("bl_level"):
            # Use data_source level as default
            options["bl_level"] = options["level"]

        if not options.get("bl_pk"):
            if None in itemgetter("bl_type", "bl_level")(options):
                raise ValueError(
                    "Either bl_pk or all [bl_type, bl_level] values must be set."
                )

        sp = transaction.savepoint()
        logging.debug("Saved transaction savepoint.")

        data_source_cls = options.get("source")

        if issubclass(data_source_cls, OnlineDataSource) and not options.get("uri"):
            options.pop("uri")
            data_source = data_source_cls.from_online_source(**options)
        else:
            data_source = data_source_cls(**options)

        boundary_layer = None
        if bl_pk := options.get("bl_pk"):
            boundary_layer = BoundaryLayer.objects.get(pk=bl_pk)
        else:
            _boundary_owner = None
            if options.get("bl_boundary_pk"):
                _boundary_owner = Boundary.objects.filter(
                    pk=options.get("bl_boundary_pk")
                ).first()
            boundary_layer = BoundaryLayer(
                boundary=_boundary_owner,
                boundary_type=options.get("bl_type"),
                name=data_source.level_name,
                level=options.get("bl_level"),
                description=data_source.level_description,
            )
            boundary_layer.parent = (
                BoundaryLayer.objects.filter(pk=options.get("bl_parent_pk")).first()
                or BoundaryLayer.objects.filter(
                    boundary_type=options.get("bl_type"),
                    level__lt=options.get("bl_level"),
                    boundary=_boundary_owner,
                )
                .order_by("level")
                .last()
            )
            boundary_layer.save()

        logging.info(f"Using boundary_layer with pk {boundary_layer.pk}")
        logging.info(
            "Using boundary_layer parent with pk {}".format(
                getattr(boundary_layer.parent, "pk", None)
            )
        )

        dataset = ZippedShapefileFormat().create_dataset(in_stream=data_source.ds)
        kwargs = dict(
            boundary_layer=boundary_layer,
            name_fieldname=data_source.name_field_name,
            code_fieldname=data_source.code_field_name,
        )
        result = BoundaryResource(show_progess_bar=True).import_data(
            dataset,
            dry_run=options.get("dry_run"),
            raise_errors=True,
            use_transactions=True,
            collect_failed_rows=True,
            rollback_on_validation_errors=False,
            **kwargs,
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
