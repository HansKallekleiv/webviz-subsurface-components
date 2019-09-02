import os
import json
import timeit
import io
import base64
from PIL import Image
from PIL import ImageFilter
import numpy as np
import pandas as pd
from matplotlib import cm
import xtgeo
from uuid import uuid4
import dash
import dash_html_components as html
import dash_core_components as dcc
from dash.dependencies import Input, Output
import webviz_subsurface_components
from webviz_config.common_cache import cache

# @cache.memoize(timeout=cache.TIMEOUT)
def array_to_png(Z, shift=True, colormap=False):
    '''The layered map dash component takes in pictures as base64 data
    (or as a link to an existing hosted image). I.e. for containers wanting
    to create pictures on-the-fly from numpy arrays, they have to be converted
    to base64. This is an example function of how that can be done.

    1) Scale the input array (Z) to the range 0-255.
    2) If shift=True and colormap=False, the 0 value in the scaled range
       is reserved for np.nan (while the actual data points utilize the
       range 1-255.

       If shift=True and colormap=True, the 0 value in the colormap range
       has alpha value equal to 0.0 (i.e. full transparency). This makes it
       possible for np.nan values in the actual map becoming transparent in
       the image.
    3) If the array is two-dimensional, the picture is stored as greyscale.
       Otherwise it is either stored as RGB or RGBA (depending on if the size
       of the third dimension is three or four, respectively).
    '''
    start = timeit.timeit()
    Z -= np.nanmin(Z)

    if shift:
        Z *= 254.0/np.nanmax(Z)
        Z += 1.0
    else:
        Z *= 255.0/np.nanmax(Z)

    Z[np.isnan(Z)] = 0

    if colormap:
        if Z.shape[0] != 1:
            raise ValueError('The first dimension of a '
                             'colormap array should be 1')
        if Z.shape[1] != 256:
            raise ValueError('The second dimension of a '
                             'colormap array should be 256')
        if Z.shape[2] not in [3, 4]:
            raise ValueError('The third dimension of a colormap '
                             'array should be either 3 or 4')
        if shift:
            if Z.shape[2] != 4:
                raise ValueError('Can not shift a colormap which '
                                 'is not utilizing alpha channel')
            else:
                Z[0][0][3] = 0.0  # Make first color channel transparent

    if Z.ndim == 2:
        image = Image.fromarray(np.uint8(Z), 'L')
    elif Z.ndim == 3:
        if Z.shape[2] == 3:
            image = Image.fromarray(np.uint8(Z), 'RGB')
        elif Z.shape[2] == 4:
            image = Image.fromarray(np.uint8(Z), 'RGBA')
        else:
            raise ValueError('Third dimension of array must '
                             'have length 3 (RGB) or 4 (RGBA)')
    else:
        raise ValueError('Incorrect number of dimensions in array')
    # image = image.filter(ImageFilter.SMOOTH)
    byte_io = io.BytesIO()
    image.save(byte_io, format='png')
    # image.save('out.png', format='png')
    byte_io.seek(0)

    base64_data = base64.b64encode(byte_io.read()).decode('ascii')
    end = timeit.timeit()
    t = end - start
    return f'data:image/png;base64,{base64_data}'

# @cache.memoize(timeout=cache.TIMEOUT)
def get_colormap(colormap):
    return array_to_png(cm.get_cmap(colormap, 256)
                            ([np.linspace(0, 1, 256)]), colormap=True)


# @cache.memoize(timeout=cache.TIMEOUT)
class SurfaceLeafletLayer():

    def __init__(self, name, fn, calc=None):
        self.name = name
        self.arr = self.get_surface_array(fn, calc)
        self.colormap = self.set_colormap('viridis')

    def get_surface_array(self, fn, calc=None):
        print(fn)
        if isinstance(fn, list):
            slist = []
            for el in fn:
                s = xtgeo.surface.RegularSurface(el, fformat='irap_binary')
                slist.append(s.values)
                nparr = np.array(slist)
            if calc == 'average':
                npavg = np.average((nparr), axis=0)
                s.values = npavg
            if calc == 'diff':
                # nparr =
                npdiff = np.subtract(np.array(slist)[1], np.array(slist)[0])
                s.values = npdiff
        else:
            s = xtgeo.surface.RegularSurface(fn, fformat='irap_binary')
        s.unrotate()
        xi, yi, zi = s.get_xyz_values()
        xi = np.flip(xi.transpose(), axis=0)
        yi = np.flip(yi.transpose(), axis=0)
        zi = np.flip(zi.transpose(), axis=0)
        return [xi, yi, zi]

    def set_colormap(self, colormap):
        return get_colormap(colormap)

    @property
    def bounds(self):
        return [[np.min(self.arr[0]), np.min(self.arr[1])],
                [np.max(self.arr[0]), np.max(self.arr[1])]]

    @property
    def center(self):
        return [np.mean(self.arr[0]), np.mean(self.arr[1])]

    @property
    def z_arr(self):
        return self.arr[2].filled(np.nan)

    @property
    def as_png(self):
        return array_to_png(self.z_arr)

    @property
    def leaflet_layer(self):
        return {'name': self.name,
                'checked': True,
                'base_layer': True,
                'data':[{'type': 'image',
                         'url': self.as_png,
                         'colormap': self.colormap,
                         'bounds': self.bounds,
                        }]
                }

class SeismicFenceLeafletLayer():

    def __init__(self, name, fence, cube_name):
        self.name = name
        self.fence = fence
        hmin, hmax, vmin, vmax, values = self.get_cfence(cube_name)
        self.vmin = vmin
        self.vmax = vmax
        self.hmin = hmin
        self.hmax = hmax

        self.bounds = [[0, 0], [1000,1000]]
        self.center = [500, 500]
        self.z_arr = values
        self.colormap = self.set_colormap('RdBu')

    def get_h_layer(self, fn):
        s = xtgeo.surface.RegularSurface(fn, fformat='irap_binary')
        values = s.get_randomline(self.fence.values.copy())
        
        x =np.interp(values[:,0], (self.hmin, self.hmax), (0, 1000))
        y =np.interp(values[:,1], (self.vmin, self.vmax), (0, 1000))
        y = [(1000)-a for a in y]
        # data = [np.interp(x, (x.min(), x.max()), (0, 1000)), self.vmax-np.interp(y, (y.min(), y.max()), (0, 1000))+self.vmin]
        data = [[a, b] for a, b in zip(x,y)]

        return {
                    'name': 'surface',
                    'checked': True,
                    'base_layer': False,
                    'data': [{'type': 'polyline',
                            'positions': data,
                            'color': 'black',
                            'tooltip': fn}]
                }


    def get_cfence(self, cube_name):
        cube = xtgeo.cube.Cube(cube_name)
        print(f'loaded cube {cube_name}')
        return cube.get_randomline(self.fence.values.copy())

    def get_wfence(self, well_name, nextend=2, tvdmin=0) -> pd.DataFrame:
        '''Generate 2D array along well path'''
        df = self.well_to_df(well_name)
        keep = ("X_UTME", "Y_UTMN", "Z_TVDSS")
        for col in df.columns:
            if col not in keep:
                df.drop(labels=col, axis=1, inplace=True)
        df["POLY_ID"] = 1
        df["NAME"] = well_name
        poly = xtgeo.Polygons()
        poly.dataframe = df
        poly.name = well_name

        if tvdmin is not None:
            poly.dataframe = poly.dataframe[poly.dataframe[poly.zname] >= tvdmin]
        data = poly.get_fence(nextend=nextend,  atleast=1000,     asnumpy=True)
        df = pd.DataFrame(data)
        df.columns = df.columns.astype(str)
        return df

    def well_to_df(self, well_name) -> pd.DataFrame:
        return xtgeo.well.Well(well_name).dataframe

    def set_colormap(self, colormap):
        return get_colormap(colormap)

    @property
    def as_png(self):
        return array_to_png(self.z_arr)

    @property
    def leaflet_layer(self):
        return {'name': self.name,
                'checked': True,
                'base_layer': True,
                'hill_shading': False,
                'data':[{'type': 'image',
                         'url': self.as_png,
                         'colormap': self.colormap,
                         'bounds': self.bounds,
                         # 'hill_shading': hillshade
                        }]
                }

class GridFenceLeafletLayer():

    def __init__(self, name, fence,  grid_path, para_path):
        self.name = name
        self.fence = fence
        hmin, hmax, vmin, vmax, values = self.get_gfence(grid_path, para_path)
        self.vmin = vmin
        self.vmax = vmax
        self.hmin = hmin
        self.hmax = hmax
        self.bounds = [[0, 0], [1000, 1000]]
        self.center = [1000/2, 1000/2]
        self.z_arr = values
        self.colormap = self.set_colormap('viridis')

    def get_h_layer(self, fn):
        s = xtgeo.surface.RegularSurface(fn, fformat='irap_binary')
        values = s.get_randomline(self.fence.values.copy())
        
        x =np.interp(values[:,0], (self.hmin, self.hmax), (0, 1000))
        y =np.interp(values[:,1], (self.vmin, self.vmax), (0, 1000))
        y = [(1000)-a for a in y]
        # data = [np.interp(x, (x.min(), x.max()), (0, 1000)), self.vmax-np.interp(y, (y.min(), y.max()), (0, 1000))+self.vmin]
        data = [[a, b] for a, b in zip(x,y)]

        return {
                    'name': 'surface',
                    'checked': True,
                    'base_layer': False,
                    'data': [{'type': 'polyline',
                            'positions': data,
                            'color': 'black',
                            'tooltip': fn}]
                }

    def get_grid(self, g_name):
        grid = xtgeo.grid3d.Grid(g_name)
        geom = grid.get_geometrics(return_dict=True)
        return (grid, geom)

    def get_parameter(self, p_name):
        return xtgeo.grid3d.GridProperty().from_file(p_name, fformat="roff")
        
    
    def get_gfence(self, g_name, p_name):
        '''Slice cube along well fence'''
    
        grid, geom = self.get_grid(g_name)
        print(f'loaded grid {g_name}')
        parameter = self.get_parameter(p_name)
        print(f'loaded parameter {g_name}')
        # return
        return grid.get_randomline(
            self.fence.values.copy(), parameter,
            zmin=geom['zmin'], zmax=geom['zmax'], zincrement=2.0)


    def get_wfence(self, well_name, nextend=2, tvdmin=0) -> pd.DataFrame:
        '''Generate 2D array along well path'''
        df = self.well_to_df(well_name)
        keep = ("X_UTME", "Y_UTMN", "Z_TVDSS")
        for col in df.columns:
            if col not in keep:
                df.drop(labels=col, axis=1, inplace=True)
        df["POLY_ID"] = 1
        df["NAME"] = well_name
        poly = xtgeo.Polygons()
        poly.dataframe = df
        poly.name = well_name

        if tvdmin is not None:
            poly.dataframe = poly.dataframe[poly.dataframe[poly.zname] >= tvdmin]
        data = poly.get_fence(nextend=nextend,  atleast=1000,     asnumpy=True)
        df = pd.DataFrame(data)
        df.columns = df.columns.astype(str)
        return df

    def well_to_df(self, well_name) -> pd.DataFrame:
        return xtgeo.well.Well(well_name).dataframe

    def set_colormap(self, colormap):
        return get_colormap(colormap)

    @property
    def as_png(self):
        return array_to_png(self.z_arr)

    @property
    def leaflet_layer(self):
        return {'name': self.name,
                'checked': True,
                'base_layer': True,
                'hill_shading': False,
                'data':[{'type': 'image',
                         'url': self.as_png,
                         'colormap': self.colormap,
                         'bounds': self.bounds,
                         # 'hill_shading': hillshade
                        }]
                }


class SeismicFence():
    ### A leaflet webviz container


    def __init__(self, app):
        self.uid = uuid4()
        self.chart_id = f'chart-id-{self.uid}'
        self.chart_id2 = f'chart-id2-{self.uid}'
        self.real_id = f'real-id-{self.uid}'
        self.type_id = f'type-id-{self.uid}'
        self.scratch= '/scratch/troll_fmu/hakal/reek/realization-'
        self.reals = [0, 1,2,3,4]
        self.surfpath = '/iter-0/share/results/maps/topreek--depthsurface.gri'
        self.seispath = '/iter-0/share/results/seismic/seismic--3dseis_depth--19910701.segy'
        self.gridpath = '/iter-0/share/results/grids/eclgrid.roff'
        self.parapath = '/iter-0/share/results/grids/eclgrid--poro.roff'
        self.geogridpath = '/iter-0/share/results/grids/geogrid.roff'
        self.geoparapath = '/iter-0/share/results/grids/geogrid--phit.roff'
        self.surface = self.scratch+str(self.reals[0])+self.surfpath
        self.seismic = self.scratch+str(self.reals[0])+self.seispath
        

        self.s = SurfaceLeafletLayer(self.surface, self.surface)
        self.center = self.s.center
        self.colormap = get_colormap('viridis')
        self.set_callbacks(app)

    @property
    def layout(self):
        return html.Div(style={'display': 'grid',
                                'gridTemplateColumns': '1fr 1fr'},children=[
            webviz_subsurface_components.LayeredMap(
                id=self.chart_id,
                map_bounds=self.s.bounds,
                center=self.center,
                layers=[self.s.leaflet_layer]),
            html.Div(children=[
                dcc.RadioItems(
                        id=self.real_id,
                        options=[{'label': f'Realization: {str(r)}' , 'value': str(r)} for r in self.reals],
            
                            value=str(self.reals[0]),
                            labelStyle={'display': 'inline-block'}
                        ) ,
                dcc.RadioItems(
                        id=self.type_id,
                        options=[{'label': r , 'value': r} for r in ['seismic', 'simgrid']],
            
                            value='seismic',
                            labelStyle={'display': 'inline-block'}
                        ) ,
                webviz_subsurface_components.LayeredMap(
                    id=self.chart_id2,
                    map_bounds=self.s.bounds,
                    center=self.center,
                    layers=[]),
                ])])


    def set_callbacks(self, app):
        @app.callback([Output(self.chart_id2, 'layers'),
                       Output(self.chart_id2, 'map_bounds'),
                       Output(self.chart_id2, 'center')],
                       [Input(self.real_id, 'value'), 
                        Input(self.type_id, 'value'),
                        Input(self.chart_id, 'line_points')])
        def change_map(real, viztype, coords):
            if not coords:
                return [], [[]], [0,0]

            coords_dict = [{'X_UTME':c[1], 'Y_UTMN':c[0], 'Z_TVDSS':0} for c in coords]
            df = pd.DataFrame().from_dict(coords_dict)
            df["POLY_ID"] = 1
            df["NAME"] = 'test'
            poly = xtgeo.Polygons()
            poly.dataframe = df
            data = poly.get_fence(asnumpy=True)
            df = pd.DataFrame(data)
            surface = self.scratch+str(real)+self.surfpath
            df.columns = df.columns.astype(str)
            if viztype == 'seismic':
                seismic = self.scratch+str(real)+self.seispath
                s = SeismicFenceLeafletLayer('seismic', df, seismic)

            if viztype == 'simgrid':

                gridpath = self.scratch+str(real)+self.gridpath
                parapath = self.scratch+str(real)+self.parapath
                s = GridFenceLeafletLayer('grid', df, gridpath, parapath)
            if viztype == 'geogrid':

                gridpath = self.scratch+str(real)+self.geogridpath
                parapath = self.scratch+str(real)+self.geoparapath
                s = GridFenceLeafletLayer('grid', df, gridpath, parapath)
    
            h = s.get_h_layer(surface)
            return [s.leaflet_layer, h], s.bounds, s.center

if __name__ == '__main__':
    app = dash.Dash(__name__)
    app.config.suppress_callback_exceptions = True
    container = SeismicFence(app)
    app.layout = container.layout
    app.run_server(host='0.0.0.0', debug=True)
