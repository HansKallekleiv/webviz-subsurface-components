import React, { Component } from 'react';
import { MapControl, withLeaflet } from 'react-leaflet';
import  {EditControl}  from 'react-leaflet-draw';
import "./assets/leaflet.draw.css";
import L from 'leaflet';


// work around broken icons when using webpack, see https://github.com/PaulLeCam/react-leaflet/issues/255

delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: require('leaflet/dist/images/marker-icon-2x.png'),
  iconUrl: require('leaflet/dist/images/marker-icon.png'),
  shadowUrl: require('leaflet/dist/images/marker-shadow.png'),
});


class DrawControls extends Component {

  _onEdited = (e) => {

    e.layers.eachLayer( (layer) => {
          const coords = layer._latlngs.map(p => {
            return [p.lat, p.lng]
        })
        this.props.lineCoords(coords)
    })
  }

  deleteAllLayers() {
  
      var {edit} = this.refs;
      var layerContainer = edit.leafletElement.options.edit.featureGroup
      var layers = layerContainer._layers
      var layer_ids = Object.keys(layers)
      let layer
      for (var i = 0; i < layer_ids.length-1; i++) {
          layer = layers[layer_ids[i]]._leaflet_id
          layerContainer.removeLayer(layer);
        }
  }
  
  _onCreated = (e) => {
    let type = e.layerType;
    let layer = e.layer;
    if (type === 'marker') {
        this.props.markerCoords([e.layer._latlng.lat, e.layer._latlng.lng])
    }
    else {
        const coords = e.layer._latlngs.map(p => {
            return [p.lat, p.lng]
        })
        this.props.lineCoords(coords)
        this.deleteAllLayers()
    }
  }

  _onDeleted = (e) => {

    let numDeleted = 0;
    e.layers.eachLayer( (layer) => {
      numDeleted += 1;
    });
    console.log(`onDeleted: removed ${numDeleted} layers`, e);
  }

  _onMounted = (drawControl) => {
    console.log('_onMounted', drawControl);
  }

  _onEditStart = (e) => {
    console.log('_onEditStart', e);
  }

  _onEditStop = (e) => {
    console.log('_onEditStop', e);
  }

  _onDeleteStart = (e) => {
    console.log('_onDeleteStart', e);
  }

  _onDeleteStop = (e) => {
    console.log('_onDeleteStop', e);
  }


  render() {
    return (
            <EditControl
              ref={"edit"}
              position='topright'
              onEdited={this._onEdited}
              onCreated={this._onCreated}
              onDeleted={this._onDeleted}
              onMounted={this._onMounted}
              onEditStart={this._onEditStart}
              onEditStop={this._onEditStop}
              onDeleteStart={this._onDeleteStart}
              onDeleteStop={this._onDeleteStop}
              draw={{
                  rectangle: false,
                  circle: false,
                  polygon:false
              }}
            />
    );
  }
}
export default withLeaflet(DrawControls)
