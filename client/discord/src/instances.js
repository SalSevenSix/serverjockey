'use strict';

const fetch = require('node-fetch');
const logger = require('./logger.js');
const util = require('./util.js');
const servers = {
  projectzomboid: require('./servers/projectzomboid.js'),
  factorio: require('./servers/factorio.js')
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
    // TODO subscribe for instance updates
    this.#channel = channel;
    this.#instances = await fetch(this.#context.config.SERVER_URL + '/instances')
      .then(function(response) {
        if (!response.ok) throw new Error('Status: ' + response.status);
        return response.json();
      })
      .then(function(json) {
        return json;
      })
      .catch(logger.error);
    this.#current = util.getFirstKey(this.#instances);
    for (let instance in this.#instances) {
      this.#instances[instance].server = servers[this.#instances[instance].module];
      this.#instances[instance].server.startup(this.#context, channel, instance, this.#instances[instance].url);
    }
    logger.info('Instances...');
    logger.raw(this.#instances);
  }

  currentInstance() {
    return this.#current;
  }

  createInstance(data) {
    let instance = data.identity;
    this.#instances[instance] = {
      module: data.module,
      server: servers[data.module],
      url: this.#context.config.SERVER_URL + '/instances/' + instance
    };
    this.#current = instance;
    this.#instances[instance].server.startup(this.#context, this.#channel, instance, this.#instances[instance].url);
  }

  useInstance(instance) {
    if (this.#instances.hasOwnProperty(instance)) {
      this.#current = instance;
    }
  }

  getData(instance) {
    if (instance == null) return null;
    if (!this.#instances.hasOwnProperty(instance)) return null;
    return this.#instances[instance];
  }

  deleteInstance(instance) {
    if (this.#instances.hasOwnProperty(instance)) {
      delete this.#instances[instance]
      if (instance === this.#current) {
        this.#current = util.getFirstKey(this.#instances);
      }
    }
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
