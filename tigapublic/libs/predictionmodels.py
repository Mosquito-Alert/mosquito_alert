# -*- coding: utf-8 -*-
"""Storm Drain Libraries."""
from .base import BaseManager
from tigapublic.constants import gridsize


class predictionModels(BaseManager):
    """Manage prediction models."""

    def __init__(self, year=None, month=None):
        """Instantiate class ."""
        self.data = None
        if year is None or month is None:
            return False

    def getSdGeometries(self):
        """Build BBox geometries."""
        geoms = []
        for row in self.data.dict:
            # All model columns required
            if (row['lon'] is not None and
                    row['lat'] is not None and
                    row['prob_median'] is not None and
                    row['sd'] is not None):

                # Do geojson geometry
                geoms.append({
                    'type': 'Feature',
                    'geometry': {
                        'type': 'Point',
                        'coordinates': [
                            round(float(row['lon'])+(gridsize/2), 3),
                            round(float(row['lat'])+(gridsize/2), 3)
                            ]
                    },
                    'properties': {'val': round(float(row['sd']), 2)}
                })
        response = {"type": "FeatureCollection", "features": geoms}
        return response

    def getProbGeometries(self):
        """Build Point geometries."""
        geoms = []

        for row in self.data.dict:
            # All model columns required
            if (row['lon'] is not None and
                    row['lat'] is not None and
                    row['prob_median'] is not None and
                    row['sd'] is not None):

                # Do geojson geometry
                min_lon = round(float(row['lon']), 3)
                min_lat = round(float(row['lat']), 3)
                max_lon = round(float(row['lon']) + gridsize, 3)
                max_lat = round(float(row['lat']) + gridsize, 3)
                geoms.append({
                    'type': 'Feature',
                    'geometry': {
                        'type': 'Polygon',
                        'coordinates': [[
                            [min_lon, min_lat], [max_lon, min_lat],
                            [max_lon, max_lat], [min_lon, max_lat],
                            [min_lon, min_lat]
                        ]]
                    },
                    'properties': {'prob': round(float(row['prob_median']), 2),
                                   'sd': round(float(row['sd']), 2)}
                })

        response = {"type": "FeatureCollection", "features": geoms}
        return response
