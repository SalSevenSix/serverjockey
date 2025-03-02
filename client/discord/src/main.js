import EventEmitter from 'events'; EventEmitter.defaultMaxListeners = 24;
import fs from 'fs';
import { Client, GatewayIntentBits, Partials, version as djsver } from 'discord.js';
import * as cutil from 'common/util/util';
import * as util from './util/util.js';
import * as logger from './util/logger.js';
import * as http from './util/http.js';
import * as system from './system.js';
import * as instances from './instances.js';

const context = { running: false };

function initialise() {
  const metarg = process.argv.length > 2 ? process.argv[2] : null;
  if (metarg == null || metarg === '-h' || metarg === '--help') {
    console.log('usage: serverlink [-h|--help] [-v|--version] [config1.json config2.json ...]');
    process.exit(metarg == null ? 1 : 0);
  }
  const version = '0.18.0 ({timestamp})';
  if (metarg === '-v' || metarg === '--version') {
    console.log(version);
    process.exit(0);
  }
  let [config, homedir] = [{}, null];
  for (const path of process.argv.slice(2)) {
    config = { ...config, ...JSON.parse(fs.readFileSync(path)) };
    if (path.endsWith('serverlink.json')) { homedir = path; }
  }
  if (!config.BOT_TOKEN) {
    logger.error('Failed to start ServerLink. Discord token not set. Please update configuration.');
    process.exit(1);
  }
  if (!config.DATADIR) {
    if (homedir) {
      homedir = homedir.substring(0, homedir.lastIndexOf('/'));
      config.DATADIR = (homedir ? homedir : '.') + '/data';
    } else {
      logger.error('Failed to start ServerLink. No DATADIR is provided or can be found.');
      process.exit(1);
    }
  }
  if (!fs.existsSync(config.DATADIR)) { fs.mkdirSync(config.DATADIR); }
  logger.info('*** START ServerLink Bot ***');
  config.ADMIN_ROLE = util.listifyRoles(config.ADMIN_ROLE);
  config.PLAYER_ROLE = util.listifyRoles(config.PLAYER_ROLE);
  const tlsKey = 'NODE_TLS_REJECT_UNAUTHORIZED';
  if (process.env[tlsKey] != 0 && config.SERVER_URL.startsWith('https')) {
    process.env[tlsKey] = 0;
  }
  logger.info('Version: ' + version);
  logger.info('Executable: ' + process.argv[0]);
  logger.info('JS Runtime: ' + process.version);
  logger.info('discord.js: ' + djsver);
  logger.info(tlsKey + ': ' + process.env[tlsKey]);
  logger.info('Initialised with config...');
  logger.dump(config);
  return config;
}

function startup() {
  context.running = true;
  logger.info('Logged in as ' + context.client.user.tag);
  const channelConfig = context.config.EVENT_CHANNELS;
  const channels = { server: null, login: null, chat: null };
  Object.keys(channels).forEach(function(channelType) {
    if (cutil.hasProp(channelConfig, channelType) && channelConfig[channelType]) {
      channels[channelType] = channelConfig[channelType];
    }
  });
  let promises = [...new Set(Object.values(channels))];
  promises = promises.filter(function(channelId) { return channelId; });
  promises = promises.map(function(channelId) {
    return context.client.channels.fetch(channelId).then(function(channel) { return channel; }).catch(logger.error);
  });
  Promise.all(promises).then(function(results) {
    const channelMap = {};
    results.forEach(function(channel) {
      if (channel) { channelMap[channel.id] = channel; }
    });
    Object.keys(channels).forEach(function(channelType) {
      const channelId = channels[channelType];
      channels[channelType] = null;
      if (channelId && cutil.hasProp(channelMap, channelId)) {
        channels[channelType] = channelMap[channelId];
        logger.info('Publishing ' + channelType + ' events to ' + channels[channelType].name + ' (' + channelId + ')');
      }
    });
    context.instancesService.startup(channels).then(function() { logger.info('ServerLink Bot has STARTED'); });
  });
}

function handleMessage(message) {
  if (!message.content.startsWith(context.config.CMD_PREFIX)) return;
  if (!message.member || !message.member.user) return;  // Broken message
  logger.info(message.member.user.tag + ' ' + message.content);
  const data = util.commandLineToList(message.content.slice(context.config.CMD_PREFIX.length));
  if (data.length === 0) return util.reactUnknown(message);
  let command = data.shift().toLowerCase();
  let instance = context.instancesService.currentInstance();
  const parts = command.split('.');
  if (parts.length === 2) { [instance, command] = parts; }
  if (command === 'startup') return util.reactUnknown(message);
  const args = { context: context, instance: instance, message: message, data: data };
  const instanceData = context.instancesService.getData(instance);
  if (instanceData && instanceData.server && cutil.hasProp(instanceData.server, command)) {
    args.httptool = new http.MessageHttpTool(context, message, instanceData.url);
    [args.aliases, args.rewards] = [instanceData.aliases, instanceData.rewards];
    instanceData.server[command](args);
  } else if (cutil.hasProp(system, command)) {
    args.httptool = new http.MessageHttpTool(context, message, context.config.SERVER_URL);
    system[command](args);
  } else {
    util.reactUnknown(message);
  }
}

function shutdown() {
  logger.info('Shutdown ServerLink');
  if (!context.running) return;
  context.running = false;
  context.controller.abort();
  context.client.destroy();
  logger.info('*** END ServerLink Bot ***');
}

export function main() {
  context.config = initialise();
  context.controller = new AbortController();
  context.signal = context.controller.signal;
  context.instancesService = new instances.Service(context);
  context.client = new Client({
    intents: [
      GatewayIntentBits.Guilds, GatewayIntentBits.GuildMembers, GatewayIntentBits.GuildMessages,
      GatewayIntentBits.MessageContent, GatewayIntentBits.DirectMessages],
    partials: [Partials.Channel]
  });
  context.client.once('ready', startup);
  context.client.on('messageCreate', handleMessage);
  process.on('SIGTERM', shutdown);
  process.on('SIGINT', shutdown);
  context.shutdown = shutdown;
  context.client.login(context.config.BOT_TOKEN);
}
