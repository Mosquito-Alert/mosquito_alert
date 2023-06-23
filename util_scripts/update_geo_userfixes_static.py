import django
from django.conf import settings

import pandas as pd
import os, sys

proj_path = "/home/webuser/webapps/tigaserver/"
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "tigaserver_project.settings")
sys.path.append(proj_path)

django.setup()

from tigaserver_app.models import Fix


FILE = os.path.join(settings.STATIC_ROOT, "geo_user_fixes.csv")

# Getting all fixes and create a new DataFrame.
# Selecting only the desired fields for speed reasons.
df = pd.DataFrame.from_records(
    Fix.objects.all().values('server_upload_time', 'masked_lon', 'masked_lat')
)

# Remove any NaN value
df.dropna(inplace=True)

# Rename the datetime colume to a more readable name
df.rename(
    columns={"server_upload_time": "datetime"}, 
    inplace=True
)

# Convert datetime column to just date
df['datetime'] = pd.to_datetime(df['datetime']).dt.normalize()
# Round float to 2 decimals (lat and lon)
df = df.round(decimals=2)

##########
# Group by date, lat, lon and count the number of elements
# to make the resulting file smaller.
##########
# If the dataviz is slow, create bins for the latitude and longitue.
# Example: https://stackoverflow.com/questions/39254704/pandas-group-bins-of-data-per-longitude-latitude
# import numpy as np
# degres_step = 0.1
# to_bin = lambda x: np.floor(x / step) * step
# df["latBin"] = to_bin(df.masked_lat)
# df["lonBin"] = to_bin(df.masked_lon)

# See: https://pandas.pydata.org/pandas-docs/stable/user_guide/timeseries.html
df.groupby(
    [
        pd.Grouper(key='datetime', freq='3W-MON'), # Every 3 weeks.
        df['masked_lon'],
        df['masked_lat']
    ]).size()\
    .reset_index(name='count')\
    .to_csv(FILE, index=False)