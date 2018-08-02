# -*- coding: utf-8 -*-
"""Storm Drain Libraries."""
from base import BaseManager
from tigapublic.utils import julianDay, urlExists
from tigapublic.constants import (gridsize, prediction_models_folder,
                                  prediction_file_head_name,
                                  prediction_file_tail_name,
                                  prediction_days_ahead, prediction_models_url)
from datetime import datetime, timedelta, date


class predictionModels(BaseManager):
    """Manage prediction models."""

    def __init__(self, mydate=None):
        """Instantiate class ."""
        self.data = None
        if mydate is None:
            self.date = date.today()
        else:
            mydate = datetime.strptime(mydate, '%Y-%m-%d').date()
            self.date = mydate

    def getDate(self):
        """Get date instance."""
        return self.date

    def getNextPredictionDates(self):
        """Get Prediction Data. Date format %Y-%m-%d."""
        # today and six days ahead
        available_dates = []
        for x in range(prediction_days_ahead):
            nextdate = self.date + timedelta(days=x)
            year = nextdate.year
            jDay = julianDay(nextdate)
            # filename = (prediction_models_folder + str(year) + '\\' +
            #             prediction_file_head_name + str(jDay) +
            #             prediction_file_tail_name)
            filename = (prediction_models_url + str(year) + '/' +
                        prediction_file_head_name + str(jDay) +
                        prediction_file_tail_name)
            print filename
            if urlExists(filename):
                available_dates.append(str(nextdate))

            # if os.path.isfile(filename):
            #     print nextdate
            #     files.append(str(nextdate))

        return available_dates

    def getSdGeometries(self):
        """Build BBox geometries."""
        geoms = []
        for row in self.data.dict:
            # All model columns required
            if (row['lon'] is not None and
                    row['lat'] is not None and
                    row['tiga_prob'] is not None and
                    row['tiga_prob_sd'] is not None):

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
                    'properties': {'val': round(float(row['tiga_prob_sd']), 2)}
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
                    row['tiga_prob'] is not None and
                    row['tiga_prob_sd'] is not None):

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
                    'properties': {'prob': round(float(row['tiga_prob']), 2),
                                   'sd': round(float(row['tiga_prob_sd']), 2)}
                })

        response = {"type": "FeatureCollection", "features": geoms}
        return response
