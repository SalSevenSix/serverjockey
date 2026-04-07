import * as cutil from 'common/util/util';
import * as io from '../util/io.js';

function getArgValue(key, arg) {
  if (!arg || !arg.startsWith(key + '=')) return null;
  return arg.substring(key.length + 1);
}

/* eslint-disable max-lines-per-function */
export function newTriggers(context, instance) {
  const file = context.config.DATADIR + '/' + instance + '.trigger.json';
  const data = { base: [] };
  const self = {};

  self.load = function() {
    io.fileRead(file, function(body) { data.base = JSON.parse(body); });
    return self;
  };

  self.reset = function() {
    data.base = [];
    return self;
  };

  self.save = function() {
    io.fileSaveArray(file, data.base);
  };

  self.add = function(args) {
    if (!args) return false;
    const record = {};
    record['on-event'] = args.filter(function(arg) {  // Capture events
      return ['on-login', 'on-logout', 'on-death', 'on-started', 'on-stopped'].includes(arg);
    });
    if (record['on-event'].length === 0) return false;  // At least one event required
    args.forEach(function(arg) {  // Capture member conditions
      if (arg === 'rq-member') { record['rq-member'] = true; }
      if (arg === 'rq-not-member') { record['rq-member'] = false; }
    });
    let [actions, value] = [0, null];
    ['rq-not-role', 'rq-role'].forEach(function(key) {  // Capture role conditions
      args.forEach(function(arg) {
        value = getArgValue(key, arg);
        if (value) {
          if (!cutil.hasProp(record, key)) { record[key] = []; }
          record[key].push(JSON.parse(value));
        }
      });
    });
    args.forEach(function(arg) {  // Capture context values
      value = getArgValue('cx-channel', arg);
      if (value) { record['cx-channel'] = JSON.parse(value); }
      value = getArgValue('cx-delay', arg);
      if (value) { value = parseInt(value, 10); }
      if (value && !isNaN(value) && value > 1) { record['cx-delay'] = value; }
    });
    ['do-remove-role', 'do-add-role', 'do-message', 'do-dm'].forEach(function(key) {  // Capture role actions
      args.forEach(function(arg) {
        value = getArgValue(key, arg);
        if (value) {
          if (!cutil.hasProp(record, key)) { record[key] = []; }
          record[key].push(key.endsWith('role') ? JSON.parse(value) : value);
          actions += 1;
        }
      });
    });
    if (actions === 0) return false;  // At least one action required
    data.base.push(record);
    return true;
  };

  self.remove = function(key) {
    if (!key) return false;
    const index = parseInt(key, 10);
    if (isNaN(index) || index < 0 || index >= data.base.length) return false;
    data.base.splice(index, 1);
    return true;
  };

  self.listText = function() {
    if (data.base.length === 0) return ['No Triggers'];
    return data.base.map(function(record, index) {
      const result = [];
      let line = [index.toString(), '|'];
      for (const [key, values] of Object.entries(record)) {
        if (result.length === 0 && key.startsWith('do-')) {
          result.push(line.join(' '));
          line = ['  >'];
        }
        for (const value of Array.isArray(values) ? values : [values]) {
          if (line.length > 1 && key === 'do-message') {
            result.push(line.join(' '));
            line = ['  >'];
          }
          if (key === 'on-event') { line.push(value.toString()); }
          else if (key === 'rq-member') { line.push('rq' + (value ? '-' : '-not-') + 'member'); }
          else if (key.includes('channel') && value.name) { line.push(key + '=#' + value.name); }
          else if (key.includes('role') && value.name) { line.push(key + '=@' + value.name); }
          else { line.push(key + '=' + value.toString()); }
        }
      }
      result.push(line.join(' '));
      return result.join('\n');
    });
  };

  self.list = function() {
    return data.base.map(function(record) { return { ...record }; });
  };

  return self;
}
/* eslint-enable max-lines-per-function */
