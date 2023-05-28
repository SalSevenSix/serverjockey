'use strict';

function initialise() {
  let config = {};
  for (let i = 2; i < process.argv.length; i++) {
    config = { ...config, ...require(process.argv[i]) };
  }
  if (!config.BOT_TOKEN) {
    logger.error('Failed to start ServerLink. Discord token not set. Please update configuration.')
    process.exit(1)
  }
  logger.info('*** START ServerLink Bot ***');
  logger.info('Version: 0.1.0');
  logger.info('Initialised with config...');
  logger.raw(config);
  return config;
}

function startup() {
  context.running = true;
  logger.info('Logged in as ' + context.client.user.tag);
  if (!context.config.EVENTS_CHANNEL_ID) {
    context.instancesService.startup(null);
    return;
  };
  context.client.channels.fetch(context.config.EVENTS_CHANNEL_ID)
    .then(function(channel) {
      logger.info('Publishing events to ' + channel.id);
      context.instancesService.startup(channel);
    })
    .catch(logger.error);
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
  let args = { context: context, instance: instance, message: message, data: data };
  let instanceData = context.instancesService.getData(instance);
  if (instanceData && instanceData.server && command != 'startup' && instanceData.server.hasOwnProperty(command)) {
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
process.env['NODE_TLS_REJECT_UNAUTHORIZED'] = 0;
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
