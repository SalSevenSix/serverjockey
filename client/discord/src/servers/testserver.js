'use strict';

const commons = require('../commons.js');
const helpText = {
  title: 'TEST SERVER COMMANDS',
  help1: [
    'server            : Server status',
    'server start      : Start server',
    'server restart    : Save world and restart server',
    'server stop       : Save world and stop server',
    'auto {mode}       : Set auto mode, valid values 0,1,2,3',
    'log               : Get last 100 lines from the log',
    'players           : Show players currently online',
    'send {line}       : Send command to server console',
    'getconfig cmdargs : Get cmd args as attachment',
    'setconfig cmdargs : Update cmd args using attached file',
    'deployment backup-runtime    : Backup server to zip file',
    'deployment install-runtime {version} : Install game server'
  ],
  send: '/console/help'
};


exports.startup = commons.startAllEventLogging;
exports.help = function($) { commons.sendHelp($, helpText); }
exports.server = commons.server;
exports.auto = commons.auto;
exports.log = commons.log;
exports.getconfig = commons.getconfig;
exports.setconfig = commons.setconfig;
exports.deployment = commons.deployment;
exports.players = commons.players;
exports.send = commons.send;
