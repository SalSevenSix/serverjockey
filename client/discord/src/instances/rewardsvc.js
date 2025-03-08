import fs from 'fs';
import * as cutil from 'common/util/util';
import * as logger from '../util/logger.js';

/* eslint-disable max-lines-per-function */
export function newRewards(context, instance) {
  const file = context.config.DATADIR + '/' + instance + '.reward.json';
  const data = { base: [] };
  const self = {};

  const unpack = function(value) {
    const record = { action: value.action, snowflake: value.snowflake, roleid: value.roleid,
      type: value.type, threshold: value.threshold, range: value.range };
    record.toString = function() {
      return record.action + ' @' + record.roleid + ' ' + record.type + ' ' + record.threshold + ' ' + record.range;
    };
    return record;
  };

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

  self.add = function(action, snowflake, roleid, type, threshold, range) {
    if (!snowflake || !roleid) return false;
    if (!['give', 'take'].includes(action)) return false;
    if (!['played', 'top'].includes(type)) return false;
    if (type === 'played' && !cutil.rangeCodeToMillis(threshold)) return false;
    if (type === 'top' && !(/^\d*$/).test(threshold)) return false;
    if (!cutil.rangeCodeToMillis(range)) return false;
    data.base.push({ action, snowflake, roleid, type, threshold, range });
    return true;
  };

  self.move = function(key, positions) {
    if (!key || !positions) return false;
    const result = cutil.moveArrayElement(data.base, key, positions);
    if (result == data.base) return false;
    data.base = result;
    return true;
  };

  self.remove = function(key) {
    if (!key) return false;
    const index = parseInt(key, 10);
    if (isNaN(index) || index < 0 || index >= data.base.length) return false;
    data.base.splice(index, 1);
    return true;
  };

  self.list = function() {
    return data.base.map(function(value) { return unpack(value); });
  };

  self.listText = function() {
    if (data.base.length === 0) return ['No Rewards'];
    return data.base.map(function(value, index) { return index + ' | ' + unpack(value).toString(); });
  };

  return self;
}
/* eslint-enable max-lines-per-function */
