import React, {Component} from 'react';
import PropTypes from 'prop-types';
import {InputLabel, Input, FormControl, FormHelperText, Select, MenuItem} from '@material-ui/core';

const parseData = data => (typeof data === 'string' ? JSON.parse(data) : data);

class SurfaceSelector extends Component {
    constructor(props) {
        super(props)
        this.data = parseData(this.props.data)
        this.state = {'property':'', 'zonation':[], 'dates': [], 'zone':'', 'date':''}
        this.setProperty = this.setProperty.bind(this)
    }

    setProperty(e) {
        const property = e.target.value
        const prevZone = this.state.zone
        const prevDate = this.state.date
        
        const zonation = this.getZonation(property)
        const dates = this.getDates(property)
        let zone
        let date
        if (zonation) {
            if (zonation.includes(prevZone)) {
                zone = prevZone
            }
            else {
                zone = zonation[0]
            }
        }
        else {
            zone = null
        }
        if (dates) {
            if (dates.includes(prevDate)) {
                date = prevDate
            }
            else {
                date = dates[0]
            }
        }
        else {
            date = null
        }
        
        
        
        this.setState({property, zone, date, zonation, dates})
    }

    getZonation(property) {
        return this.data[property].hasOwnProperty('zonation') ? this.data[property].zonation : null
    }

    getDates(property) {
        return this.data[property].hasOwnProperty('dates') ? this.data[property].dates : null
    }
    render() {
        const properties = Object.keys(this.data)
        
        return (<div>
            <FormControl>
                 <InputLabel htmlFor="property-helper">Surface Property</InputLabel>
                 <Select
                        value={this.state.property}
                        onChange={this.setProperty}
                        inputProps={{
                            name: 'property',
                            id: 'property-helper',
                        }}
                >
                    {properties.map(prop => {
                        return <MenuItem key={prop} value={prop}>{prop}</MenuItem>
                    })}
                </Select>
                
        </FormControl>
                    <FormControl>
                
                 <InputLabel htmlFor="zone-helper">Surface Name</InputLabel>
                 <Select
                        value={this.state.zone}
                        
                        inputProps={{
                            name: 'zone',
                            id: 'zone-helper',
                        }}
                >
                    {this.state.zonation.map(prop => {
                        return <MenuItem key={prop} value={prop}>{prop}</MenuItem>
                    })}
                </Select>

                
        </FormControl>
                            <FormControl>
                
                 <InputLabel htmlFor="date-helper">Surface Name</InputLabel>
                 <Select
                        value={this.state.date}
                        
                        inputProps={{
                            name: 'date',
                            id: 'date-helper',
                        }}
                >
                    {this.state.dates.map(prop => {
                        return <MenuItem key={prop} value={prop}>{prop}</MenuItem>
                    })}
                </Select>

                
        </FormControl>
        </div>
        )
    }
}

SurfaceSelector.defaultProps = {
    height: 800,
};

SurfaceSelector.propTypes = {
    id: PropTypes.string.isRequired,
    
    data: PropTypes.object,
    
    
};

export default SurfaceSelector;
