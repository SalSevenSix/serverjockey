'use strict';

const commons = require('../commons.js');
const helpText = {
  help: [
    'server            : Server status',
    'server daemon     : Start server with auto-restart',
    'server start      : Start server',
    'server restart    : Save world and restart server',
    'server stop       : Save world and stop server',
    'players           : Show players currently online',
    'getconfig cmdargs : Get cmd args as attachment',
    'getconfig server  : Get server settings as attachment',
    'getconfig map     : Get map settings as attachment',
    'getconfig mapgen  : Get map-gen settings as attachment',
    'getconfig adminlist : Get adminlist as attachment',
    'getconfig whitelist : Get whitelist as attachment',
    'getconfig banlist   : Get banlist as attachment',
    'setconfig cmdargs : Update cmd args using attached file',
    'setconfig server  : Update server using attached file',
    'setconfig map     : Update map using attached file',
    'setconfig mapgen  : Update map-gen using attached file',
    'setconfig adminlist : Update adminlist using attached file',
    'setconfig whitelist : Update whitelist using attached file',
    'setconfig banlist   : Update banlist using attached file',
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
  let s = '```\nFACTORIO COMMANDS\n' + x.config.CMD_PREFIX;
  c.send(s + helpText.help.join('\n' + x.config.CMD_PREFIX) + '```');
  return;
}
