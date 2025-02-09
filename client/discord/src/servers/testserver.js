const helptext = require('../helptext.js');
const commons = require('../commons.js');
const helpText = {
  title: 'TEST SERVER COMMANDS',
  help1: [
    'server            : Server status',
    'server start      : Start server',
    'server restart    : Save world and restart server',
    'server restart-after-warnings : Warnings then restart server',
    'server restart-on-empty       : Restart when server is empty',
    'server stop       : Save world and stop server',
    'auto {mode}       : Set auto mode, valid values 0,1,2,3',
    'log               : Get last 100 lines from the log',
    'players           : Show players currently online',
    'send {line}       : Send command to server console',
    'getconfig cmdargs : Get cmd args as attachment',
    'setconfig cmdargs : Update cmd args using attached file',
    'activity {query ...}  : Activity, use help for details',
    'deployment backup-runtime     : Backup server to zip file',
    'deployment install-runtime {version} : Install game server'
  ],
  send: '/console/help',
  activity: helptext.activity
};

export const startup = commons.startAllEventLogging;
export function help($) { commons.sendHelp($, helpText); }
export const server = commons.server;
export const auto = commons.auto;
export const log = commons.log;
export const getconfig = commons.getconfig;
export const setconfig = commons.setconfig;
export const deployment = commons.deployment;
export const players = commons.players;
export const send = commons.send;
export const activity = commons.activity;
