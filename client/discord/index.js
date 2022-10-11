'use strict';

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
      if (context.config.STARTUP_REPORT) {
        fs.promises.access(context.config.STARTUP_REPORT, fs.constants.F_OK)
          .then(function() {
            logger.info('Sending startup report.');
            channel.send({
              content: '**Startup Report**',
              files: [{ attachment: context.config.STARTUP_REPORT, name: 'report.text' }] });
          })
          .catch(function() {
            logger.info('No startup report found.');
          });
      }
    })
    .catch(logger.error);
}

function handleMessage(message) {
  //if (message.author.bot) return;
  if (!message.content.startsWith(context.config.CMD_PREFIX)) return;
  if (!message.member || !message.member.user) return;  // broken message
  logger.info(message.member.user.tag + ' ' + message.content);
  let data = util.commandLineToList(message.content.slice(1))
  let command = data.shift().toLowerCase();
  let instance = context.instancesService.currentInstance();
  let parts = command.split('.');
  if (parts.length === 1) {
    command = parts[0];
  } else {
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
  message.react('⛔');
}

function shutdown() {
  if (!context.running) return;
  context.running = false;
  context.controller.abort();
  context.client.destroy();
  logger.info('*** END ServerLink Bot ***');
}


// MAIN
process.env['NODE_TLS_REJECT_UNAUTHORIZED'] = 0;
const fs = require('fs');
const fetch = require('node-fetch');
const { Client, Intents } = require('discord.js');
const logger = require('./src/logger.js');
const util = require('./src/util.js');
const http = require('./src/http.js');
const system = require('./src/system.js');
const instances = require('./src/instances.js');

logger.info('*** START ServerLink Bot ***');
const context = { running: false };
context.staticData = require('./src/constants.json');
context.config = { ...require(process.argv[2]), ...require(process.argv[3]) };
if (!context.config.BOT_TOKEN) throw new Error('BOT_TOKEN not set');
logger.info('Initialised with config...');
logger.raw(context.config);

context.controller = new AbortController();
context.signal = context.controller.signal;
context.instancesService = new instances.Service(context);
context.client = new Client({ intents: ['GUILDS', 'GUILD_MESSAGES', 'DIRECT_MESSAGES'], partials: ['CHANNEL'] });

context.client.once('ready', startup);
context.client.on('messageCreate', handleMessage);
process.on('SIGTERM', shutdown);
context.shutdown = shutdown;

context.client.login(context.config.BOT_TOKEN);
