import fs from 'fs';
import fetch from 'node-fetch';
import * as cutil from 'common/util/util';
import * as util from './util/util.js';
import * as logger from './util/logger.js';
import * as subs from './util/subs.js';
import * as aliassvc from './instances/aliassvc.js';
import * as rewardsvc from './instances/rewardsvc.js';
import * as triggersvc from './instances/triggersvc.js';
import * as servers from './servers.js';

async function fetchJson(context, url) {
  return await fetch(url, util.newGetRequest(context.config.SERVER_TOKEN))
    .then(function(response) {
      if (!response.ok) throw new Error('Status: ' + response.status);
      return response.json();
    })
    .then(function(json) { return json; })
    .catch(logger.error);
}

export class Service {
  #context;

  #modules = {};

  #instances = {};

  #current = null;

  constructor(context) {
    this.#context = context;
  }

  async startup(channels) {
    const [self, context] = [this, this.#context];
    const [baseurl, currentFile] = [context.config.SERVER_URL, context.config.DATADIR + '/current.json'];
    const [modules, instances] = await Promise.all([
      fetchJson(context, baseurl + '/modules'), fetchJson(context, baseurl + '/instances')]);
    [this.#modules, this.#instances, this.#current] = [modules, instances, util.getFirstKey(instances)];
    if (fs.existsSync(currentFile)) {
      const currentData = JSON.parse(fs.readFileSync(currentFile));
      if (currentData && cutil.hasProp(instances, currentData.instance)) { this.#current = currentData.instance; }
    }
    for (const [identity, instance] of Object.entries(instances)) {
      instance.aliases = aliassvc.newAliases(context, identity).load();
      instance.rewards = rewardsvc.newRewards(context, identity).load();
      instance.triggers = triggersvc.newTriggers(context, identity).load();
      instance.server = servers[instance.module];
      instance.server.startup({ context: context, channels: channels, instance: identity, url: instance.url,
        aliases: instance.aliases, triggers: instance.triggers });
    }
    logger.info('Instances...');
    logger.raw(self.getInstancesText().join('\n'));
    new subs.Helper(context).daemon(baseurl + '/instances/subscribe', function(data) {
      const identity = data.instance.identity;
      if (data.event === 'created') {
        const instance = data.instance;
        logger.info('Event create instance: ' + identity + ' (' + instance.module + ')');
        instance.url = baseurl + '/instances/' + identity;
        instance.aliases = aliassvc.newAliases(context, identity);
        instance.rewards = rewardsvc.newRewards(context, identity);
        instance.triggers = triggersvc.newTriggers(context, identity);
        instance.server = servers[instance.module];
        instances[identity] = instance;
        instance.server.startup({ context: context, channels: channels, instance: identity, url: instance.url,
          aliases: instance.aliases, triggers: instance.triggers });
      } else if (data.event === 'deleted' && cutil.hasProp(instances, identity)) {
        logger.info('Event delete instance: ' + identity + ' (' + instances[identity].module + ')');
        instances[identity].aliases.reset().save();
        instances[identity].rewards.reset().save();
        instances[identity].triggers.reset().save();
        delete instances[identity];
        if (identity === self.currentInstance()) { self.useInstance(util.getFirstKey(instances), true); }
      }
      return true;
    });
  }

  currentInstance() {
    return this.#current;
  }

  useInstance(instance, force = false) {
    if (!force && !cutil.hasProp(this.#instances, instance)) return false;
    if (this.#current === instance) return true;
    this.#current = instance;
    const [currentFile, currentData] = [this.#context.config.DATADIR + '/current.json', { instance: instance }];
    fs.writeFile(currentFile, JSON.stringify(currentData), logger.error);
    return true;
  }

  getData(instance) {
    if (!instance || !cutil.hasProp(this.#instances, instance)) return null;
    return this.#instances[instance];
  }

  getModule(instance) {
    const instanceData = this.getData(instance);
    return instanceData ? instanceData.module : null;
  }

  getModuleName(instance) {
    const module = this.getModule(instance);
    if (!module || !cutil.hasProp(this.#modules, module)) return null;
    return this.#modules[module];
  }

  getModulesText() {
    return Object.keys(this.#modules);
  }

  getInstancesText() {
    if (Object.keys(this.#instances).length === 0) return ['No instances found'];
    const [result, currentInstance] = [[], this.currentInstance()];
    for (const [identity, data] of Object.entries(this.#instances)) {
      result.push((identity === currentInstance ? '=> ' : '   ') + identity + ' (' + data.module + ')');
    }
    return result;
  }
}
