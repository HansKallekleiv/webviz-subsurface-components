import glob

import flask
import geojson
import numpy as np
import xtgeo
from flask import send_file
import dash
import webviz_subsurface_components as wsc

from utils.xtgeo_surface_to_float32 import get_surface_float32
from utils.xtgeo_wells_to_json import xtgeo_wells_to_geojson
from utils.xtgeo_polygons_to_json import xtgeo_polygons_to_polylines_geojson

# Import a depth surface
depth_surface = xtgeo.surface_from_file("examples/example-data/topvolantis_depth.gri")

# Import wells
wells = [
    xtgeo.well_from_file(wellfile, mdlogname="MDepth")
    for wellfile in glob.glob("examples/example-data/*.rmswell")
]

polygons = xtgeo.polygons_from_file(
    "examples/example-data/topvolantis_faultpolygons.pol"
)

app = dash.Dash(__name__)

app.layout = dash.html.Div(
    children=[
        wsc.DeckGLMap(
            id="deckgl-map",
            bounds=[456150, 5925800, 467400, 5939500],
            layers=[
                {
                    "@@type": "WellsLayer",
                    "id": "wells-layer",
                    "data": "/wells/wells.json",
                    "refine": False,
                },
                {
                    "@@type": "FaultPolygonsLayer",
                    "id": "fault-layer",
                    "data": "/faults/faults.json",
                    "refine": False,
                },
                {
                    "@@type": "LassoLayer",
                    "visible": True,
                    "pickable": True,
                    "data": xtgeo_wells_to_geojson(
                        wells
                    ),  # Duplication of data? Cannot use URI here
                },
            ],
            editedData={},
        ),
        dash.html.Div(id="box-out", children=[""]),
    ]
)


@app.callback(
    dash.Output("box-out", "children"), [dash.Input("deckgl-map", "editedData")]
)
def get_edited_data(edited_data):
    print(edited_data)
    return edited_data


@app.server.route("/wells/wells.json")
def send_wells():
    featurecol = xtgeo_wells_to_geojson(wells)
    return flask.Response(geojson.dumps(featurecol), mimetype="application/geo+json")


if __name__ == "__main__":
    app.run_server(debug=True)
