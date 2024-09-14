'use strict';

function initialise() {
  const metarg = process.argv.length > 2 ? process.argv[2] : null;
  if (metarg == null || metarg === '-h' || metarg === '--help') {
    console.log('usage: serverlink [-h|--help] [-v|--version] [config1.json config2.json ...]');
    process.exit(metarg == null ? 1 : 0);
  }
  const version = '0.13.0 ({timestamp})';
  if (metarg === '-v' || metarg === '--version') {
    console.log(version);
    process.exit(0);
  }
  let config = {};
  for (let i = 2; i < process.argv.length; i++) {
    config = { ...config, ...require(process.argv[i]) };
  }
  if (!config.BOT_TOKEN) {
    logger.error('Failed to start ServerLink. Discord token not set. Please update configuration.');
    process.exit(1);
  }
  logger.info('*** START ServerLink Bot ***');
  config.ADMIN_ROLE = util.listifyRoles(config.ADMIN_ROLE);
  config.PLAYER_ROLE = util.listifyRoles(config.PLAYER_ROLE);
  const tls_key = 'NODE_TLS_REJECT_UNAUTHORIZED';
  if (process.env[tls_key] != 0 && config.SERVER_URL.startsWith('https')) {
    process.env[tls_key] = 0;
  }
  logger.info('Version: ' + version);
  logger.info('Executable: ' + process.argv[0]);
  logger.info('JS Runtime: ' + process.version);
  logger.info('discord.js: ' + require('./node_modules/discord.js/package.json').version);
  logger.info(tls_key + ': ' + process.env[tls_key]);
  logger.info('Initialised with config...');
  logger.dump(config);
  return config;
}

function startup() {
  context.running = true;
  logger.info('Logged in as ' + context.client.user.tag);
  const configChannels = context.config.EVENT_CHANNELS;
  const channelIds = new Set();
  if (configChannels.server) { channelIds.add(configChannels.server); }
  if (configChannels.login) { channelIds.add(configChannels.login); }
  if (configChannels.chat) { channelIds.add(configChannels.chat); }
  const promises = [];
  for (let channelId of channelIds.values()) {
    promises.push(context.client.channels.fetch(channelId)
      .then(function(channel) { return channel; })
      .catch(logger.error));
  }
  Promise.all(promises).then(function(channels) {
    const channelsMap = {};
    for (let index in channels) {
      if (channels[index]) { channelsMap[channels[index].id] = channels[index]; }
    }
    const startupArgs = { server: null, login: null, chat: null };
    if (configChannels.server && channelsMap.hasOwnProperty(configChannels.server)) {
      startupArgs.server = channelsMap[configChannels.server];
      logger.info('Publishing server events to ' + startupArgs.server.name + ' (' + startupArgs.server.id + ')');
    }
    if (configChannels.login && channelsMap.hasOwnProperty(configChannels.login)) {
      startupArgs.login = channelsMap[configChannels.login];
      logger.info('Publishing login events to ' + startupArgs.login.name + ' (' + startupArgs.login.id + ')');
    }
    if (configChannels.chat && channelsMap.hasOwnProperty(configChannels.chat)) {
      startupArgs.chat = channelsMap[configChannels.chat];
      logger.info('Publishing chat events to ' + startupArgs.chat.name + ' (' + startupArgs.chat.id + ')');
    }
    context.instancesService.startup(startupArgs)
      .then(function() { logger.info('ServerLink Bot has STARTED'); });
  });
}

function handleMessage(message) {
  //if (message.author.bot) return;
  if (!message.content.startsWith(context.config.CMD_PREFIX)) return;
  if (!message.member || !message.member.user) return;  // broken message
  logger.info(message.member.user.tag + ' ' + message.content);
  const data = util.commandLineToList(message.content.slice(context.config.CMD_PREFIX.length));
  if (data.length === 0) {
    message.react('❓');
    return;
  }
  let command = data.shift().toLowerCase();
  let instance = context.instancesService.currentInstance();
  const parts = command.split('.');
  if (parts.length > 1) {
    command = parts[1];
    instance = parts[0];
  }
  if (command === 'startup') {
    message.react('❓');
    return;
  }
  const args = { context: context, instance: instance, message: message, data: data };
  const instanceData = context.instancesService.getData(instance);
  if (instanceData && instanceData.server && instanceData.server.hasOwnProperty(command)) {
    if (command === 'help' && data.length === 0) {
      system.help(args);
    }
    args.httptool = new http.MessageHttpTool(context, message, instanceData.url);
    instanceData.server[command](args);
    return;
  }
  if (system.hasOwnProperty(command)) {
    args.httptool = new http.MessageHttpTool(context, message, context.config.SERVER_URL);
    system[command](args);
    return;
  }
  message.react('❓');
}

function shutdown() {
  logger.info('Shutdown ServerLink');
  if (!context.running) return;
  context.running = false;
  context.controller.abort();
  context.client.destroy();
  logger.info('*** END ServerLink Bot ***');
}


// MAIN
require('events').EventEmitter.defaultMaxListeners = 20;
const { Client, GatewayIntentBits, Partials } = require('discord.js');
const logger = require('./src/logger.js');
const util = require('./src/util.js');
const http = require('./src/http.js');
const system = require('./src/system.js');
const instances = require('./src/instances.js');

const context = { running: false };
context.config = initialise();
context.controller = new AbortController();
context.signal = context.controller.signal;
context.instancesService = new instances.Service(context);
context.client = new Client({
  intents: [GatewayIntentBits.Guilds, GatewayIntentBits.GuildMessages,
            GatewayIntentBits.MessageContent, GatewayIntentBits.DirectMessages],
  partials: [Partials.Channel] });

context.client.once('ready', startup);
context.client.on('messageCreate', handleMessage);
process.on('SIGTERM', shutdown);
process.on('SIGINT', shutdown);
context.shutdown = shutdown;

context.client.login(context.config.BOT_TOKEN);
