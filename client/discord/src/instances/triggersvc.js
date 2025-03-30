import fs from 'fs';
import * as cutil from 'common/util/util';
import * as logger from '../util/logger.js';

function migration(file, loadedData) {
  if (!loadedData || loadedData.length === 0) return loadedData;  // Nothing to migrate
  if (cutil.hasProp(loadedData[0], 'on-event')) return loadedData;  // Already in new format
  const records = loadedData.map(function(loaded) {
    const record = {};
    record['on-event'] = Object.keys(loaded).filter(function(key) {  // Convert events
      return ['on-login', 'on-logout', 'on-death'].includes(key);
    });
    ['rq-not-role', 'rq-role'].forEach(function(key) {  // Convert conditions
      if (cutil.hasProp(loaded, key)) { record[key] = [loaded[key]]; }
    });
    ['cx-channel', 'cx-delay'].forEach(function(key) {  // Convert context
      if (cutil.hasProp(loaded, key)) { record[key] = loaded[key]; }
    });
    ['do-remove-role', 'do-add-role', 'do-message'].forEach(function(key) {  // Convert actions
      if (cutil.hasProp(loaded, key)) { record[key] = [loaded[key]]; }
    });
    return record;
  });
  fs.writeFile(file, JSON.stringify(records), logger.error);
  return records;
}

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
    fs.exists(file, function(exists) {
      if (!exists) return;
      fs.readFile(file, function(error, body) {
        if (error) return logger.error(error);
        data.base = migration(file, JSON.parse(body));
      });
    });
    return self;
  };

  self.reset = function() {
    data.base = [];
    return self;
  };

  self.save = function() {
    fs.writeFile(file, JSON.stringify(data.base), logger.error);
  };

  self.add = function(args) {
    if (!args) return false;
    const record = {};
    record['on-event'] = args.filter(function(arg) {  // Capture events
      return ['on-login', 'on-logout', 'on-death', 'on-started', 'on-stopped'].includes(arg);
    });
    if (record['on-event'].length === 0) return false;  // At least one event required
    let [actions, value] = [0, null];
    ['rq-not-role', 'rq-role'].forEach(function(key) {  // Capture conditions
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
    ['do-remove-role', 'do-add-role', 'do-message'].forEach(function(key) {  // Capture actions
      args.forEach(function(arg) {
        value = getArgValue(key, arg);
        if (value) {
          if (!cutil.hasProp(record, key)) { record[key] = []; }
          record[key].push(key === 'do-message' ? value : JSON.parse(value));
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
          let displayValue = value;
          if (key.includes('channel') && value.name) { displayValue = '#' + value.name; }
          else if (key.includes('role') && value.name) { displayValue = '@' + value.name; }
          line.push(key === 'on-event' ? displayValue.toString() : key + '=' + displayValue.toString());
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
