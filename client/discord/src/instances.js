'use strict';

const fetch = require('node-fetch');
const logger = require('./logger.js');
const util = require('./util.js');
const subs = require('./subs.js');
const servers = {
  projectzomboid: require('./servers/projectzomboid.js'),
  factorio: require('./servers/factorio.js'),
  sevendaystodie: require('./servers/sevendaystodie.js'),
  unturned: require('./servers/unturned.js')
};

exports.Service = class Service {
  #context;
  #channel = null;
  #current = null;
  #instances = {};

  constructor(context) {
    this.#context = context;
  }

  async startup(channel) {
    this.#channel = channel;
    let self = this;
    let context = this.#context;
    let baseurl = context.config.SERVER_URL;
    let instances = await fetch(baseurl + '/instances')
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
    for (let instance in instances) {
      instances[instance].server = servers[instances[instance].module];
      instances[instance].server.startup(context, channel, instance, instances[instance].url);
    }
    logger.info('Instances...');
    logger.raw(instances);
    new subs.Helper(context).daemon(baseurl + '/instances/subscribe', function(data) {
      if (data.event === 'created') {
        data.instance.url = baseurl + '/instances/' + data.instance.identity;
        data.instance.server = servers[data.instance.module];
        instances[data.instance.identity] = data.instance;
        data.instance.server.startup(context, channel, data.instance.identity, data.instance.url);
      } else if (data.event === 'deleted') {
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
    if (this.#instances.hasOwnProperty(instance)) {
      this.setInstance(instance);
    }
  }

  getData(instance) {
    if (instance == null) return null;
    if (!this.#instances.hasOwnProperty(instance)) return null;
    return this.#instances[instance];
  }

  getInstancesText() {
    let instances = Object.keys(this.#instances);
    if (instances.length === 0) {
      return '```No instances found.```';
    }
    let result = '```';
    for (let i = 0; i < instances.length; i++) {
      if (instances[i] === this.#context.instancesService.currentInstance()) {
        result += '=> ';
      } else {
        result += '   ';
      }
      result += instances[i] + '\n';
    }
    result += '```';
    return result;
  }

}
