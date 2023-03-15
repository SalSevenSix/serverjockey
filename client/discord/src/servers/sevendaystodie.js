'use strict';

const commons = require('../commons.js');
const helpText = {
  help: [
    'server             : Server status',
    'server daemon      : Start server with auto-restart',
    'server start       : Start server',
    'server restart     : Save world and restart server',
    'server stop        : Save world and stop server',
    'players            : Show players currently online',
    'getconfig settings : Get settings as attachment',
    'getconfig admin    : Get admin settings as attachment',
    'setconfig settings : Update settings using attached file',
    'setconfig admin    : Update admin settings using attached file',
    'deployment wipe-world-all    : Delete game world folder',
    'deployment wipe-world-config : Delete only config files',
    'deployment wipe-world-save   : Delete only map file',
    'deployment install-runtime   : Install game server'
  ]
};


exports.startup = commons.startupEventLogging;
exports.server = commons.server;
exports.getconfig = commons.getconfig;
exports.setconfig = commons.setconfig;
exports.deployment = commons.deployment;
exports.players = commons.players;

exports.help = function($) {
  let c = $.message.channel;
  if ($.data.length > 0) {
    c.send('No more help available.');
    return;
  }
  let x = $.context;
  let s = '```\nSEVENDAYSTODIE COMMANDS\n' + x.config.CMD_PREFIX;
  c.send(s + helpText.help.join('\n' + x.config.CMD_PREFIX) + '```');
  return;
}
