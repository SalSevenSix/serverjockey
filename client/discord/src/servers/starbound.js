'use strict';

const commons = require('../commons.js');
const helpText = {
  help: [
    'server             : Server status',
    'server daemon      : Start server with auto-restart',
    'server start       : Start server',
    'server restart     : Save world and restart server',
    'server stop        : Save world and stop server',
    'log                : Get last 100 lines from the log',
    'players            : Show players currently online',
    'send {line}        : Send command to server console',
    'getconfig settings : Get settings as attachment',
    'setconfig settings : Update settings using attached file',
    'deployment backup-world      : Backup game world to zip file',
    'deployment wipe-world-all    : Delete game world folder',
    'deployment wipe-world-save   : Delete only map files',
    'deployment install-runtime {beta} : Install game server'
  ]
};


exports.startup = commons.startupEventLogging;
exports.server = commons.server;
exports.log = commons.log;
exports.getconfig = commons.getconfig;
exports.setconfig = commons.setconfig;
exports.deployment = commons.deployment;
exports.players = commons.players;
exports.send = commons.send;

exports.help = function($) {
  let c = $.message.channel;
  if ($.data.length === 0) {
    let x = $.context;
    let s = '```\nSTARBOUND COMMANDS\n' + x.config.CMD_PREFIX;
    c.send(s + helpText.help.join('\n' + x.config.CMD_PREFIX) + '```');
    return;
  }
  if ($.data[0] === 'send') {
    $.httptool.doGet('/console/help', function(body) { return '```\n' + body + '\n```'; });
    return;
  }
  c.send('No more help available.');
}
