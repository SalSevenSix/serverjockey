const helptext = require('../helptext.js');
const commons = require('../commons.js');
const helpText = {
  title: 'STARBOUND COMMANDS',
  help1: [
    'server             : Server status',
    'server start       : Start server',
    'server restart     : Save world and restart server',
    'server stop        : Save world and stop server',
    'auto {mode}        : Set auto mode, valid values 0,1,2,3',
    'log                : Get last 100 lines from the log',
    'players            : Show players currently online',
    'send {line}        : Send command to server console',
    'getconfig cmdargs  : Get launch options as attachment',
    'getconfig settings : Get settings as attachment',
    'setconfig cmdargs  : Update launch options using attached file',
    'setconfig settings : Update settings using attached file',
    'activity {query ...}         : Activity, use help for details',
    'deployment backup-world      : Backup game world to zip file',
    'deployment wipe-world-all    : Delete game world folder',
    'deployment wipe-world-save   : Delete only map files',
    'deployment install-runtime {beta} : Install game server'
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
