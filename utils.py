"""
Utilities, ...

Some stuff is likely not needed, and will be pruned, later...
"""

import re
import os
import sys
import random
from itertools import tee

import requests
# import contextily as ctx
from geographiclib.geodesic import Geodesic
from geopy.geocoders import Here
from geopy.distance import geodesic
from ipyleaflet import Marker, CircleMarker, Polyline
from ipywidgets import HTML
# from pyproj import Proj, transform

from credentials import APP_ID, APP_CODE


app_id   = APP_ID
app_code = APP_CODE
geocoder = Here(app_id=app_id, app_code=app_code)


# Conversion between lat/lon in degrees (and zoom) to x/y/zoom as used in tile sets,
# from http://wiki.openstreetmap.org/wiki/Slippy_map_tilenames#Python

from math import radians, degrees, log, cos, tan, pi, atan, sinh

def deg2tile(lat_deg, lon_deg, zoom):
    lat_rad = radians(lat_deg)
    n = 2.0 ** zoom
    xtile = int((lon_deg + 180.0) / 360.0 * n)
    ytile = int((1.0 - log(tan(lat_rad) + (1 / cos(lat_rad))) / pi) / 2.0 * n)
    return (xtile, ytile)


# not used here
def tile2deg(xtile, ytile, zoom):
    n = 2.0 ** zoom
    lon_deg = xtile / n * 360.0 - 180.0
    lat_rad = atan(sinh(pi * (1 - 2 * ytile / n)))
    lat_deg = degrees(lat_rad)
    return (lat_deg, lon_deg)


def pairwise(iterable):
    "s -> (s0,s1), (s1,s2), (s2, s3), ..."
    a, b = tee(iterable)
    next(b, None)
    return zip(a, b)


def chunks(seq, n):
    "Yield successive n-sized chunks from l."
    # for item in zip(*(iter(seq),) * n): yield item
    for i in range(0, len(seq), n):
        yield seq[i:i + n]


# not used here
def latlon_for_address(address):
    "Return a lat/lon tuple for the given address by geocoding it."
    res = geocoder.geocode(address)
    return res.latitude, res.longitude


def build_here_tiles_url(**kwdict):
    """
    Return a HERE map tiles URL, based on default values that can be 
    overwritten by kwdict...
    
    To be used for map building services like leaflet, folium, and 
    geopandas (with additional fields inside a dict)...
    """
    params = dict(
        app_id     = app_id,
        app_code   = app_code,
        maptype    = 'traffic',
        tiletype   = 'traffictile',
        scheme     = 'normal.day',
        tilesize   = '256',
        tileformat = 'png8',
        lg         = 'eng',
        x          = '{x}',
        y          = '{y}',
        z          = '{z}',
        server     = random.choice('1234')
    )
    params.update(kwdict)
    url = (
        'https://{server}.{maptype}.maps.api.here.com'
        '/maptile/2.1/{tiletype}/newest/{scheme}/{z}/{x}/{y}/{tilesize}/{tileformat}'
        '?lg={lg}&app_id={app_id}&app_code={app_code}'
    ).format(**params)
    return url


def build_here_basemap(**kwdict):
    """
    Return a dict HERE map tiles URL, based on default values that can be 
    overwritten with params in kwdict...
    
    To be used for ipyleaflet.
    """
    params = dict(
        url = build_here_tiles_url(**kwdict),
        min_zoom = 1,
        max_zoom = 18,
        attribution = 'Tiles &copy; HERE.com',
        name = 'HERE'
    )
    params.update(kwdict)
    return params


def get_route_positions(start, end, **kwargs):
    """
    Get routing data.
    """
    lat0, lon0 = start
    lat1, lon1 = end
    params = dict(
        language='en',
        mode='fastest;car;traffic:disabled'
    )
    params.update(kwargs)
    url = (
        f'https://route.cit.api.here.com/routing/7.2/calculateroute.json'
        f'?app_id={app_id}&app_code={app_code}'
        # f'&waypoint0=street!{addr}'
        f'&waypoint0=geo!{lat0},{lon0}'
        f'&waypoint1=geo!{lat1},{lon1}'
        # f'&language={language}'
        # f'&mode=fastest;car;traffic:disabled'
        f'&metricsystem=metric'
        f'&jsonattributes=41' # ?
        # f'maneuverattributes=po,ti,pt,ac,di,fj,ix'  # ?
        f'&routeattributes=sh,gr'
        f'&instructionFormat=text' # or html
        # f'&mode=fastest;publicTransport&combineChange=true&departure=now'
    )
    for key in params:
        val = params[key]
        url += f'&{key}={val}'
    obj = requests.get(url).json()
    return obj['response']['route']
    
    leg = obj['response']['route'][0]['leg']
    res = []
    for man in leg[0]['maneuver']:
        pos = man['position']
        lat, lon = pos['latitude'], pos['longitude']
        inst = man['instruction']
        res.append(dict(lat=lat, lon=lon, maneuver=inst))
    return res


def add_route_to_map(route, some_map, color='blue'):
    """
    Add a route from the HERE REST API to the given map.
    
    This includes markers for all points where a maneuver is needed, like 'turn left'.
    And it includes a path with lat/lons from start to end and little circle markers
    around them.
    """
    path_positions = list(chunks(route[0]['shape'], 2))
    maneuvers = {
        (man['position']['latitude'], man['position']['longitude']): man['instruction']
            for man in route[0]['leg'][0]['maneuver']}

    polyline = Polyline(
        locations=path_positions,
        color=color,
        fill=False
    )
    some_map += polyline
    
    for lat, lon in path_positions:
        if (lat, lon) in maneuvers:
            some_map += CircleMarker(location=(lat, lon), radius=2)
            
            marker = Marker(location=(lat, lon), draggable=False)
            message1 = HTML()
            message1.value = maneuvers[(lat, lon)]
            marker.popup = message1
            some_map += marker
        else:
            some_map += CircleMarker(location=(lat, lon), radius=3)


def mid_point(loc1, loc2):
    """
    Calculate point in the geodesic middle between two given points. 
    """
    geod = Geodesic.WGS84
    inv_line = geod.InverseLine(*(loc1 + loc2))
    distance_m = geod.Inverse(*(loc1 + loc2))["s12"]
    loc = inv_line.Position(distance_m / 2, Geodesic.STANDARD | Geodesic.LONG_UNROLL)
    lat, lon = loc['lat2'], loc['lon2']
    return lat, lon


def bbox_for_points(coords):
    """
    Return bbox for a sequence of points.
    """
    bbox = min(coords), max(coords)
    return bbox
