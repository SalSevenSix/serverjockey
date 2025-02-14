const fs = require('fs');
const fetch = require('node-fetch');
const cutil = require('common/util/util');
const util = require('./util.js');
const logger = require('./logger.js');
const subs = require('./subs.js');
const servers = {
  testserver: require('./servers/testserver.js'),
  projectzomboid: require('./servers/projectzomboid.js'),
  factorio: require('./servers/factorio.js'),
  sevendaystodie: require('./servers/sevendaystodie.js'),
  unturned: require('./servers/unturned.js'),
  starbound: require('./servers/starbound.js'),
  csii: require('./servers/csii.js'),
  palworld: require('./servers/palworld.js')
};


/* eslint-disable max-lines-per-function */
function newAliases(context, instance) {
  const file = context.config.HOME + '/data/' + instance + '.alias.json';
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

  return self;
}


function newRewards(context, instance) {
  const file = context.config.HOME + '/data/' + instance + '.reward.json';
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
    if (!cutil.rangeCodeToMillis(threshold)) return false;
    if (!cutil.rangeCodeToMillis(range)) return false;
    data.base.push({ action, snowflake, roleid, type, threshold, range });
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


export class Service {
  #context;

  #current = null;

  #instances = {};

  constructor(context) {
    this.#context = context;
  }

  async startup(channels) {
    const [self, context, baseurl] = [this, this.#context, this.#context.config.SERVER_URL];
    const instances = await fetch(baseurl + '/instances', util.newGetRequest(context.config.SERVER_TOKEN))
      .then(function(response) {
        if (!response.ok) throw new Error('Status: ' + response.status);
        return response.json();
      })
      .then(function(json) {
        return json;
      })
      .catch(logger.error);
    this.#instances = instances;
    this.setInstance(util.getFirstKey(instances));
    for (const instance in instances) {
      instances[instance].aliases = newAliases(context, instance).load();
      instances[instance].rewards = newRewards(context, instance).load();
      instances[instance].server = servers[instances[instance].module];
      instances[instance].server.startup({ context: context, channels: channels, aliases: instances[instance].aliases,
        instance: instance, url: instances[instance].url });
    }
    logger.info('Instances...');
    logger.raw(self.getInstancesText().join('\n'));
    new subs.Helper(context).daemon(baseurl + '/instances/subscribe', function(data) {
      if (data.event === 'created') {
        data.instance.aliases = newAliases(context, data.instance.identity);
        data.instance.rewards = newRewards(context, data.instance.identity);
        data.instance.url = baseurl + '/instances/' + data.instance.identity;
        data.instance.server = servers[data.instance.module];
        instances[data.instance.identity] = data.instance;
        data.instance.server.startup({ context: context, channels: channels, aliases: data.instance.aliases,
          instance: data.instance.identity, url: data.instance.url });
      } else if (data.event === 'deleted') {
        instances[data.instance.identity].aliases.reset().save();
        instances[data.instance.identity].rewards.reset().save();
        delete instances[data.instance.identity];
        if (data.instance.identity === self.currentInstance()) {
          self.setInstance(util.getFirstKey(instances));
        }
      }
      return true;
    });
  }

  currentInstance() {
    return this.#current;
  }

  setInstance(instance) {
    this.#current = instance;
  }

  useInstance(instance) {
    if (!cutil.hasProp(this.#instances, instance)) return false;
    this.setInstance(instance);
    return true;
  }

  getData(instance) {
    if (!instance) return null;
    if (!cutil.hasProp(this.#instances, instance)) return null;
    return this.#instances[instance];
  }

  getInstancesText() {
    if (Object.keys(this.#instances).length === 0) return ['No instances found'];
    const [result, currentInstance] = [[], this.#context.instancesService.currentInstance()];
    for (const [identity, data] of Object.entries(this.#instances)) {
      result.push((identity === currentInstance ? '=> ' : '   ') + identity + ' (' + data.module + ')');
    }
    return result;
  }
}
