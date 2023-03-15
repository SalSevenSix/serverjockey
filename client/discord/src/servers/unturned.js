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
    'send {line}        : Send command to server console',
    'getconfig cmdargs  : Get command line args as attachment',
    'getconfig commands : Get server commands as attachment',
    'getconfig settings : Get general settings as attachment',
    'getconfig workshop : Get workshop mods as attachment',
    'setconfig cmdargs  : Update command line args using attached file',
    'setconfig commands : Update server commands using attached file',
    'setconfig settings : Update general settings using attached file',
    'setconfig workshop : Update workshop mods using attached file',
    'deployment wipe-world-all    : Delete game map and config',
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
exports.send = commons.send;

exports.help = function($) {
  let c = $.message.channel;
  if ($.data.length > 0) {
    if ($.data[0] === 'send') {
      $.httptool.doGet('/console/help', function(body) {
        return '```\n' + body + '\n```';
      });
      return;
    }
    c.send('No more help available.');
    return;
  }
  let x = $.context;
  let s = '```\nUNTURNED COMMANDS\n' + x.config.CMD_PREFIX;
  c.send(s + helpText.help.join('\n' + x.config.CMD_PREFIX) + '```');
  return;
}
