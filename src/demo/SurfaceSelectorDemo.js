/* eslint no-magic-numbers: 0 */
import React, {Component} from 'react';

import SurfaceSelector  from '../lib/components/SurfaceSelector';

const data = {
    "depthsurface": {"zonation": ["TopC", "TopB", "TopA", "BaseA"]},
    "pressure": {"zonation": ["TopC", "TopB", "TopA", "BaseA"], "dates":[2001, 2002, 2003]},
    "facies": {"zonation": ["TopB", "TopA", "BaseA"]}
}


class SurfaceSelectorDemo extends Component {

    render() {
        return (
            <div>
                <SurfaceSelector 
                id={'surface-select'}
                data={data} 
    
                />
            </div>
        )
    }
}

export default SurfaceSelectorDemo;
