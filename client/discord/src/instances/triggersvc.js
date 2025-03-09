import fs from 'fs';
import * as logger from '../util/logger.js';

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
        data.base = JSON.parse(body);
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
    let [counter, value] = [0, null];
    args.forEach(function(arg) {  // Capture trigger events
      if (['on-login', 'on-logout', 'on-death'].includes(arg)) {
        record[arg] = null;
        counter += 1;
      }
    });
    if (counter === 0) return false;  // At least one event required
    args.forEach(function(arg) {  // Capture trigger conditions
      ['rq-role', 'rq-not-role'].forEach(function(key) {
        value = getArgValue(key, arg);
        if (value) { record[key] = JSON.parse(value); }
      });
    });
    args.forEach(function(arg) {  // Capture context values
      value = getArgValue('cx-channel', arg);
      if (value) { record['cx-channel'] = JSON.parse(value); }
      value = getArgValue('cx-delay', arg);
      if (value) { value = parseInt(value, 10); }
      if (value && !isNaN(value) && value > 1) { record['cx-delay'] = value; }
    });
    counter = 0;
    args.forEach(function(arg) {  // Capture actions
      ['do-add-role', 'do-remove-role'].forEach(function(key) {
        value = getArgValue(key, arg);
        if (value) {
          record[key] = JSON.parse(value);
          counter += 1;
        }
      });
      value = getArgValue('do-message', arg);
      if (value) {
        record['do-message'] = value;
        counter += 1;
      }
    });
    if (counter === 0) return false;  // At least one action required
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
      let current = [index.toString(), '|'];
      for (const [key, value] of Object.entries(record)) {
        if (result.length === 0 && key.startsWith('do-') || key === 'do-message') {
          result.push(current.join(' '));
          current = ['  >'];
        }
        if (value) {
          let valueStr = value;
          if (key.includes('channel') && value.name) { valueStr = '#' + value.name; }
          else if (key.includes('role') && value.name) { valueStr = '@' + value.name; }
          current.push(key + '=' + valueStr.toString());
        } else {
          current.push(key);
        }
      }
      result.push(current.join(' '));
      return result.join('\n');
    });
  };

  self.list = function() {
    return data.base.map(function(record) { return { ...record }; });
  };

  return self;
}
/* eslint-enable max-lines-per-function */
