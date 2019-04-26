import React from 'react';
import {observer} from 'mobx-react';
import * as Rb from 'react-bootstrap';
import _ from 'lodash';
import {SettingsContext, DataContext} from './contexts.jsx';
import Consumer from './Consumer.jsx';

let LABEL_MODES = Object.freeze({
  DEFAULT: 0,
  SINGLE_IDENTITY: 1,
  TOPIC_SEGMENTS: 2
});

let SELECT_MODES = Object.freeze({
  RANGE: 0,
  INDIVIDUAL: 1
});

let labelModeToString = (i) => {
  if (i == LABEL_MODES.DEFAULT) {
    return "default";
  } else if (i == LABEL_MODES.SINGLE_IDENTITY) {
    return "single identity";
  } else if (i == LABEL_MODES.TOPIC_SEGMENTS) {
    return "topic segments";
  } else {
    throw "Invalid label mode " + i;
  }
};

let selectModeToString = (i) => {
  if (i == SELECT_MODES.RANGE) {
    return "range";
  } else if (i == SELECT_MODES.INDIVIDUAL) {
    return "individual";
  } else {
    throw "Invalid select mode " + i;
  }
};

@observer
class Options extends React.Component {
  fields = [
    {
      name: 'Results per page',
      key: 'results_per_page',
      type: 'range',
      opts: {
        step: 1,
        min: 1,
        max: 500
      }
    },
    {
      name: 'Thumbnail size',
      key: 'thumbnail_size',
      type: 'range',
      opts: {
        min: 1,
        max: 3,
        step: 1
      },
    },
    {
      name: 'Crop bboxes',
      key: 'crop_bboxes',
      type: 'radio',
      filter: (g) => false
    },

  ]

  render() {
    return <Consumer contexts={[SettingsContext, DataContext]}>{(settingsContext, dataContext) =>
      <div className='options'>
        <h2>Options</h2>
        <form>
          {this.fields.map((field, i) => {
             return (!field.filter || field.filter(dataContext[0]))
                 ?  <Rb.FormGroup key={i}>
                   <Rb.ControlLabel>{field.name}</Rb.ControlLabel>
                   {{
                      range: () => (
                        <span>
                          <input type="range" min={field.opts.min} max={field.opts.max}
                                 step={field.opts.step} value={settingsContext.get(field.key)}
                                 onChange={(e) => {
                                     if (!field.opts.disable_autoupdate) {
                                       settingsContext.set(field.key, e.target.value)
                                     }
                                 }}/>
                          {/*
                              Using the field value as a key on its container allows the field to be editable by the user
                              while still permitting programmatic modification of the value (e.g. typing into a numeric
                              field vs. moving a slider). See:
                              https://stackoverflow.com/questions/30727837/react-change-input-defaultvalue-by-passing-props--
                            */}
                          <span key={settingsContext.get(field.key)}>
                            <Rb.FormControl type="number" min={field.opts.min} max={field.opts.max}
                                            defaultValue={settingsContext.get(field.key)}
                                            onKeyPress={(e) => {
                                                if (e.key === 'Enter') {
                                                  settingsContext.set(field.key, e.target.value);
                                                }
                                            }} />
                          </span>
                        </span>),
                      radio: () => (
                        <Rb.ButtonToolbar>
                          <Rb.ToggleButtonGroup type="radio" name={field.key} defaultValue={settingsContext.get(field.key)}
                                                onChange={(e) => {settingsContext.set(field.key, e)}}>
                            <Rb.ToggleButton value={true}>Yes</Rb.ToggleButton>
                            <Rb.ToggleButton value={false}>No</Rb.ToggleButton>
                          </Rb.ToggleButtonGroup>
                        </Rb.ButtonToolbar>),
                      option: () => (
                        <Rb.FormControl componentClass="select" defaultValue={settingsContext.get(field.key)} onChange={(e) => {
                            settingsContext.set(field.key, e.target.value);
                        }}>
                          {_.zip(field.opts.keys, field.opts.values).map(([key, value]) =>
                            <option value={key} key={key}>{value}</option>)}
                        </Rb.FormControl>
                      )
                   }[field.type]()}
                 </Rb.FormGroup>
                  : <div key={i} />
          })}
        </form>
      </div>
    }</Consumer>
  }
}

@observer
class Metadata extends React.Component {
  render() {
    let keys = [
      ['ing',  [
        ['f', 'expand thumbnail'],
        ['p', 'play clip'],
        ['l', 'play clip in loop'],
        ['r', 'toggle playback speed']
      ]],
      ['Frame labeling', [
        ['click/drag', 'create bounding box'],
        ['d', 'delete bounding box'],
        ['g', 'cycle gender'],
        ['b', 'mark as background face'],
        ['s', 'select frames to save'],
        ['a', 'mark selected as labeled'],
        ['x', 'mark frame to ignore'],
        ['t', 'set identity']
      ]],
      ['Track labeling', [
        ['m', 'merge current and last track'],
        ['i', 'start/end new track'],
        ['enter', 'skip to next track'],
        ['z', 'undo last action']
      ]]
    ];

    return <DataContext.Consumer>{ dataContext =>
      <div className='metadata'>
        <h2>Help</h2>
        <div className='help'>
          On hover over a clip:
          {keys.map(([name, sec_keys], i) =>
            <div key={i} className='help-section'>
              <strong>{name}</strong>
              {sec_keys.map((entry, j) =>
                <div key={j}><code>{entry[0]}</code> - {entry[1]}</div>)}
            </div>
          )}
        </div>
      </div>
    }</DataContext.Consumer>;
  }
}

export default class Sidebar extends React.Component {
  render() {
    return <div>
      <div className='sidebar left'>
        <Metadata {...this.props} />
      </div>
      <div className='sidebar right'>
        <Options {...this.props} />
      </div>
    </div>;
  }
}
