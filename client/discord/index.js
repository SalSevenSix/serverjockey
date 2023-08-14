'use strict';

function initialise() {
  let config = {};
  for (let i = 2; i < process.argv.length; i++) {
    config = { ...config, ...require(process.argv[i]) };
  }
  if (!config.BOT_TOKEN) {
    logger.error('Failed to start ServerLink. Discord token not set. Please update configuration.');
    process.exit(1);
  }
  config.ADMIN_ROLE = util.listifyRoles(config.ADMIN_ROLE);
  config.PLAYER_ROLE = util.listifyRoles(config.PLAYER_ROLE);
  logger.info('*** START ServerLink Bot ***');
  logger.info('Version: 0.4.0 ({timestamp})');
  logger.info('Nodejs: ' + process.version);
  logger.info('discord.js: ' + require('discord.js/package.json').version);
  logger.info('Initialised with config...');
  logger.raw(JSON.stringify(config, null, 2).split('\n').slice(1, -1).join('\n'));
  if (config.SERVER_URL.startsWith('https')) {
    process.env['NODE_TLS_REJECT_UNAUTHORIZED'] = 0;
  }
  return config;
}

function startup() {
  context.running = true;
  logger.info('Logged in as ' + context.client.user.tag);
  // TODO Should probably try to await all the channel fetches, then call startup
  let channels = { server: null, login: null, chat: null };
  context.instancesService.startup(channels);
  if (context.config.EVENT_CHANNELS.server) {
    context.client.channels.fetch(context.config.EVENT_CHANNELS.server)
      .then(function(channel) {
        channels.server = channel;
        logger.info('Publishing server events to ' + channel.name + ' (' + channel.id + ')');
      })
      .catch(logger.error);
  }
  if (context.config.EVENT_CHANNELS.login) {
    context.client.channels.fetch(context.config.EVENT_CHANNELS.login)
      .then(function(channel) {
        channels.login = channel;
        logger.info('Publishing player events to ' + channel.name + ' (' + channel.id + ')');
      })
      .catch(logger.error);
  }
  if (context.config.EVENT_CHANNELS.chat) {
    context.client.channels.fetch(context.config.EVENT_CHANNELS.chat)
      .then(function(channel) {
        channels.chat = channel;
        logger.info('Publishing chat to ' + channel.name + ' (' + channel.id + ')');
      })
      .catch(logger.error);
  }
}

function handleMessage(message) {
  //if (message.author.bot) return;
  if (!message.content.startsWith(context.config.CMD_PREFIX)) return;
  if (!message.member || !message.member.user) return;  // broken message
  logger.info(message.member.user.tag + ' ' + message.content);
  let data = util.commandLineToList(message.content.slice(context.config.CMD_PREFIX.length));
  let command = data.shift().toLowerCase();
  let instance = context.instancesService.currentInstance();
  let parts = command.split('.');
  if (parts.length > 1) {
    instance = parts[0];
    command = parts[1];
  }
  if (command === 'startup') {
    message.react('❓');
    return;
  }
  let args = { context: context, instance: instance, message: message, data: data };
  let instanceData = context.instancesService.getData(instance);
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
