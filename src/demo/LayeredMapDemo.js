import React, { Component } from "react";
import LayeredMap from "../lib/components/LayeredMap";

const data = require("./example-data/layered-map.json");

class LayeredMapDemo extends Component {
        constructor(props) {
    super(props);
        this.state = { viewport: null };
    }
    setViewport(viewport) {
        this.setState({viewport:viewport})
    }
    render() {
        return (
            <div>
            <LayeredMap
                id={"layered-map-demo"}
                map_bounds={data.map_bounds}
                center={data.center}
                layers={data.layers}
                overlay_layers={data.overlay_layers}
                
                setViewport={e => this.setViewport(e)}
                viewport={this.state.viewport}
                height={400}
                draw_toolbar_marker={true}
                draw_toolbar_polygon={true}
                draw_toolbar_polyline={true}
                showScaleY={true}
            />
     <LayeredMap
                id={"layered-map-demo"}
                map_bounds={data.map_bounds}
                center={data.center}
                layers={data.layers}
                height={400}
                overlay_layers={data.overlay_layers}
                
                setViewport={e => this.setViewport(e)}
                viewport={this.state.viewport}
                draw_toolbar_marker={true}
                draw_toolbar_polygon={true}
                draw_toolbar_polyline={true}
                showScaleY={true}
            />
            </div>
        );
    }
}

export default LayeredMapDemo;
