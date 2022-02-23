# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
#
# Copyright (C) 2020 - Equinor ASA.

import io
import base64
import copy
import re
import json
from dash import Dash, html, Input, Output, State, callback, dcc

import numpy as np
from PIL import Image
import webviz_core_components as wcc
import webviz_subsurface_components as wsc


def array2d_to_png(z_array):
    """The DeckGL map dash component takes in pictures as base64 data
    (or as a link to an existing hosted image). I.e. for containers wanting
    to create pictures on-the-fly from numpy arrays, they have to be converted
    to base64. This is an example function of how that can be done.

    This function encodes the numpy array to a RGBA png.
    The array is encoded as a heightmap, in a format similar to Mapbox TerrainRGB
    (https://docs.mapbox.com/help/troubleshooting/access-elevation-data/),
    but without the -10000 offset and the 0.1 scale.
    The undefined values are set as having alpha = 0. The height values are
    shifted to start from 0.
    """

    shape = z_array.shape
    z_array = np.repeat(z_array, 4)  # This will flatten the array

    z_array[0::4][np.isnan(z_array[0::4])] = 0  # Red
    z_array[1::4][np.isnan(z_array[1::4])] = 0  # Green
    z_array[2::4][np.isnan(z_array[2::4])] = 0  # Blue

    z_array[0::4] = np.floor((z_array[0::4] / (256 * 256)) % 256)  # Red
    z_array[1::4] = np.floor((z_array[1::4] / 256) % 256)  # Green
    z_array[2::4] = np.floor(z_array[2::4] % 256)  # Blue
    z_array[3::4] = np.where(np.isnan(z_array[3::4]), 0, 255)  # Alpha

    # Back to 2d shape + 1 dimension for the rgba values.
    z_array = z_array.reshape((shape[0], shape[1], 4))
    image = Image.fromarray(np.uint8(z_array), "RGBA")

    byte_io = io.BytesIO()
    image.save(byte_io, format="png")
    byte_io.seek(0)

    # image.save("debug_image.png")

    base64_data = base64.b64encode(byte_io.read()).decode("ascii")
    return f"data:image/png;base64,{base64_data}"


if __name__ == "__main__":
    # The data below is a modified version of one of the surfaces
    # taken from the Volve data set provided by Equinor and the former
    # Volve Licence partners under CC BY-NC-SA 4.0 license, and only
    # used here as an example data set.
    # https://creativecommons.org/licenses/by-nc-sa/4.0/

    min_value = 2782.08203125
    max_value = 3513.704345703125

    WELLS = (
        "https://raw.githubusercontent.com/equinor/webviz-subsurface-components/"
        "master/react/src/demo/example-data/volve_wells.json"
    )
    LOGS = (
        "https://raw.githubusercontent.com/equinor/webviz-subsurface-components/"
        "master/react/src/demo/example-data/volve_logs.json"
    )
    with open(
        "./react/src/demo/example-data/L898MUD.json", encoding="utf8"
    ) as json_file:
        LOGS2 = json.load(json_file)

    with open(
        "./react/src/demo/example-data/welllog_template_1.json", encoding="utf8"
    ) as json_file:
        TEMPLATE = json.load(json_file)

    with open(
        "./react/src/demo/example-data/color-tables.json", encoding="utf8"
    ) as json_file:
        COLORTABLES = json.load(json_file)

    bounds = [432205, 6475078, 437720, 6481113]  # left, bottom, right, top

    map_obj = wsc.DeckGLMap(
        id="deckgl-map",
        coords={"visible": True, "multiPicking": True, "pickDepth": 10},
        scale={"visible": True},
        coordinateUnit="m",
        bounds=bounds,
        layers=[
            {
                "@@type": "Map3DLayer",
                "mesh": "https://raw.githubusercontent.com/equinor/webviz-subsurface-components/master/react/src/demo/example-data/depthMap.png",
                "bounds": [432205, 6475078, 437720, 6481113],
                "meshMaxError": 2.0,
                "propertyTexture": "https://raw.githubusercontent.com/equinor/webviz-subsurface-components/master/react/src/demo/example-data/propertyMap.png",
                "rotDeg": 0,
                "contours": [3000, 10.0],
                "colorMapName": "Physics",
                "valueRange": [2782, 3513],
                "colorMapRange": [2782, 3513],
            },
            {
                "@@type": "WellsLayer",
                "data": WELLS,
                "refine": False,
                "logData": LOGS,
                "logrunName": "BLOCKING",
                "logName": "ZONELOG",
                "logColor": "Stratigraphy",
                "selectedWell": "@@#editedData.selectedWell",
                "pickable": False,
            },
            {
                "@@type": "GridLayer",
                "id": "grid-layer",
                "data": "https://raw.githubusercontent.com/equinor/webviz-subsurface-components/master/react/src/demo/example-data/grid_layer.json",
                "colorMapName": "Rainbow",
                "valueRange": [0, 1],
                "colorMapRange": [0, 1],
                "visible": False,
            },
        ],
        editedData={
            "selectedWell": "",
            "selectedDrawingFeature": [],
            "data": {"type": "FeatureCollection", "features": []},
        },
        views={
            "layout": [1, 1],
            "viewports": [{"id": "view_1", "show3D": False, "layerIds": []}],
        },
    )

    app = Dash(__name__)

    app.layout = wcc.FlexBox(
        style={"marginRight": "0px", "width": "100vw"},
        children=[
            wcc.Frame(
                style={
                    "flex": 1,
                },
                children=[
                    wcc.Selectors(
                        label="Visualizations",
                        children=[
                            dcc.Checklist(
                                id="vis_select",
                                options=[
                                    {
                                        "label": "Map",
                                        "value": "map",
                                    },
                                    {
                                        "label": "Well log",
                                        "value": "well_log",
                                    },
                                ],
                                value=["map"],
                            )
                        ],
                    ),
                    wcc.Selectors(
                        label="Map settings",
                        open_details=False,
                        children=[
                            wcc.Selectors(
                                label="Colormap",
                                children=[
                                    wcc.Dropdown(
                                        label="Palette",
                                        id="colormap-select",
                                        options=[
                                            {
                                                "label": color,
                                                "value": color,
                                            }
                                            for color in [
                                                "Physics",
                                                "Rainbow",
                                                "Porosity",
                                                "Permeability",
                                                "Seismic BlueWhiteRed",
                                                "Time/Depth",
                                                "Stratigraphy",
                                                "Facies",
                                                "Gas-Oil-Water",
                                                "Gas-Water",
                                                "Oil-Water",
                                                "Accent",
                                            ]
                                        ],
                                        value="Physics",
                                        clearable=False,
                                    ),
                                    wcc.RangeSlider(
                                        label="Value range",
                                        id="colormap-range",
                                        min=2782,
                                        max=3513,
                                        step=1,
                                        value=[2782, 3513],
                                        updatemode="drag",
                                        tooltip={
                                            "placement": "bottom",
                                            "always_visible": True,
                                        },
                                    ),
                                ],
                            ),
                            wcc.Selectors(
                                label="Viewmode",
                                children=[
                                    wcc.RadioItems(
                                        id="viewmode",
                                        options=[
                                            {"label": "2D view", "value": "2d"},
                                            {"label": "3d view", "value": "3d"},
                                        ],
                                        value="2d",
                                    )
                                ],
                            ),
                            wcc.Selectors(
                                label="Contours",
                                children=[
                                    html.Div(
                                        style={"marginBottom": "10px"},
                                        children=[
                                            wcc.Label(
                                                children="Contour reference point"
                                            ),
                                            dcc.Input(
                                                id="contour-reference",
                                                # style={"width": "5vw"},
                                                debounce=True,
                                                value=3000.0,
                                            ),
                                        ],
                                    ),
                                    html.Div(
                                        style={"marginBottom": "10px"},
                                        children=[
                                            wcc.Label(children="Contour increment"),
                                            wcc.Slider(
                                                id="contour-slider",
                                                min=1.0,
                                                max=200.0,
                                                step=1,
                                                value=25.0,
                                                updatemode="drag",
                                                tooltip={
                                                    "placement": "bottom",
                                                    "always_visible": True,
                                                },
                                            ),
                                        ],
                                    ),
                                ],
                            ),
                        ],
                    ),
                    wcc.Selectors(
                        label="Log settings",
                        open_details=False,
                        children=[
                            wcc.Dropdown(
                                label="Log",
                                id="log-select",
                                options=[
                                    {
                                        "label": log,
                                        "value": log,
                                    }
                                    for log in [
                                        "ZONELOG",
                                        "PORO_TOT",
                                        "NTG",
                                        "PERM_TOT",
                                        "FACIES",
                                    ]
                                ],
                                value="ZONELOG",
                                clearable=False,
                            ),
                            wcc.Dropdown(
                                label="Color Palette",
                                id="log-colormap-select",
                                options=[
                                    {
                                        "label": color,
                                        "value": color,
                                    }
                                    for color in [
                                        "Physics",
                                        "Rainbow",
                                        "Porosity",
                                        "Permeability",
                                        "Seismic BlueWhiteRed",
                                        "Time/Depth",
                                        "Stratigraphy",
                                        "Facies",
                                        "Gas-Oil-Water",
                                        "Gas-Water",
                                        "Oil-Water",
                                        "Accent",
                                    ]
                                ],
                                value="Stratigraphy",
                                clearable=False,
                            ),
                        ],
                    ),
                ],
            ),
            wcc.Frame(
                id="map_wrapper",
                style={"flex": 5, "height": "90vh"},
                children=[map_obj, html.Div(id="out")],
            ),
            wcc.Frame(
                id="log_wrapper",
                style={"flex": 5, "height": "90vh", "display": "none"},
                children=[
                    wsc.WellLogViewer(
                        id="well_completions",
                        welllog=LOGS2,
                        template=TEMPLATE,
                        colorTables=COLORTABLES,
                        readoutOptions={"allTracks": True},
                    ),
                ],
            ),
        ],
    )

    @callback(
        Output("deckgl-map", "layers"),
        Input("colormap-select", "value"),
        Input("colormap-range", "value"),
        Input("contour-reference", "value"),
        Input("contour-slider", "value"),
        Input("log-select", "value"),
        Input("log-colormap-select", "value"),
        State("deckgl-map", "layers"),
    )
    def _update_layers(
        colormap,
        color_range,
        contour_ref,
        contour_inc,
        log_name,
        log_colormap,
        deckgl_layers,
    ):

        deckgl_layers[0]["colorMapName"] = colormap
        deckgl_layers[0]["colorMapRange"] = color_range
        deckgl_layers[0]["contours"] = [contour_ref, contour_inc]
        deckgl_layers[1]["logName"] = log_name
        deckgl_layers[1]["logColor"] = log_colormap
        return deckgl_layers

    @callback(
        Output("deckgl-map", "views"),
        Input("viewmode", "value"),
        State("deckgl-map", "views"),
    )
    def _update_layers(viewmode, views):

        views["viewports"][0]["show3D"] = True if viewmode == "3d" else False
        return views

    @callback(
        Output("map_wrapper", "style"),
        Output("log_wrapper", "style"),
        Input("vis_select", "value"),
        State("map_wrapper", "style"),
        State("log_wrapper", "style"),
    )
    def _update_layers(vis, map_style, log_style):

        map_style["display"] = "inline" if "map" in vis else "none"
        log_style["display"] = "inline" if "well_log" in vis else "none"
        return map_style, log_style

    app.run_server(debug=False)
