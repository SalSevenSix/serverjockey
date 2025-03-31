import fs from 'fs';
import * as cutil from 'common/util/util';
import * as util from '../util/util.js';
import * as logger from '../util/logger.js';

/* eslint-disable max-lines-per-function */
export function newAliases(context, instance) {
  const file = context.config.DATADIR + '/' + instance + '.alias.json';
  const data = { base: [], snowflake: {}, discordid: {}, name: {}, maxidlen: 0 };
  const self = {};

  const unpack = function(value) {
    const record = {};
    [record.snowflake, record.discordid, record.name] = value;
    record.toString = function() {
      return record.snowflake.padStart(19) + ' @' + record.discordid.padEnd(data.maxidlen) + ' | ' + record.name;
    };
    return record;
  };

  const rebuild = function(base) {
    [data.base, data.snowflake, data.discordid, data.name, data.maxidlen] = [base, {}, {}, {}, 0];
    data.base.sort(function(a, b) { return a[1].localeCompare(b[1]); });
    data.base.forEach(function(value) {
      const record = unpack(value);
      data.snowflake[record.snowflake] = value;
      data.discordid[record.discordid] = value;
      data.name[record.name] = value;
      if (record.discordid.length > data.maxidlen) { data.maxidlen = record.discordid.length; }
    });
  };

  self.load = function() {
    fs.exists(file, function(exists) {
      if (!exists) return;
      fs.readFile(file, function(error, body) {
        if (error) return logger.error(error);
        rebuild(JSON.parse(body));
      });
    });
    return self;
  };

  self.reset = function() {
    rebuild([]);
    return self;
  };

  self.save = function() {
    fs.writeFile(file, JSON.stringify(data.base), logger.error);
  };

  self.add = function(snowflake, discordid, name) {
    if (self.findByName(name)) return false;  // Name already aliased
    const record = self.findByKey(snowflake);
    if (record && record.discordid === discordid && record.name === name) return true;  // No change
    const base = record ? data.base.filter(function(value) {
      return unpack(value).snowflake != snowflake;
    }) : data.base;
    base.push([snowflake, discordid, name]);
    rebuild(base);
    return true;
  };

  self.remove = function(key) {
    const record = self.findByKey(key);
    if (!record) return false;  // Nothing to do
    rebuild(data.base.filter(function(value) {
      return unpack(value).snowflake != record.snowflake;
    }));
    return true;
  };

  self.listText = function() {
    if (data.base.length === 0) return ['No Aliases'];
    return data.base.map(function(value) { return unpack(value).toString(); });
  };

  self.findByKey = function(value) {
    if (!value) return null;
    const snowflake = util.toSnowflake(value);
    if (snowflake) return cutil.hasProp(data.snowflake, snowflake) ? unpack(data.snowflake[snowflake]) : null;
    const discordid = value.startsWith('@') ? value.slice(1) : value;
    return cutil.hasProp(data.discordid, discordid) ? unpack(data.discordid[discordid]) : null;
  };

  self.findByName = function(value) {
    if (!value) return null;
    return cutil.hasProp(data.name, value) ? unpack(data.name[value]) : null;
  };

  self.resolveName = function(value) {
    if (!util.toSnowflake(value)) return value;
    const record = self.findByKey(value);
    return record ? record.name : value;
  };

  return self;
}
/* eslint-enable max-lines-per-function */
