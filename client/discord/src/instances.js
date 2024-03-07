'use strict';

const fetch = require('node-fetch');
const logger = require('./logger.js');
const util = require('./util.js');
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

exports.Service = class Service {
  #context;
  #current = null;
  #instances = {};

  constructor(context) {
    this.#context = context;
  }

  async startup(channels) {
    let self = this;
    let context = this.#context;
    let baseurl = context.config.SERVER_URL;
    let instances = await fetch(baseurl + '/instances', util.newGetRequest(context.config.SERVER_TOKEN))
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
      instances[instance].server.startup(context, channels, instance, instances[instance].url);
    }
    logger.info('Instances...');
    logger.raw(self.getInstancesText().split('\n').slice(1, -1).join('\n'));
    new subs.Helper(context).daemon(baseurl + '/instances/subscribe', function(data) {
      if (data.event === 'created') {
        data.instance.url = baseurl + '/instances/' + data.instance.identity;
        data.instance.server = servers[data.instance.module];
        instances[data.instance.identity] = data.instance;
        data.instance.server.startup(context, channels, data.instance.identity, data.instance.url);
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
    if (!this.#instances.hasOwnProperty(instance)) return false;
    this.setInstance(instance);
    return true;
  }

  getData(instance) {
    if (instance == null) return null;
    if (!this.#instances.hasOwnProperty(instance)) return null;
    return this.#instances[instance];
  }

  getInstancesText() {
    if (Object.keys(this.#instances).length === 0) {
      return '```\nNo instances found.\n```';
    }
    let result = '```\n';
    for (let [identity, data] of Object.entries(this.#instances)) {
      if (identity === this.#context.instancesService.currentInstance()) {
        result += '=> ';
      } else {
        result += '   ';
      }
      result += identity + ' (' + data.module + ')\n';
    }
    return result + '```';
  }

}
