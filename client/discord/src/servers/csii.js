const helptext = require('../helptext.js');
const commons = require('../commons.js');
const helpText = {
  title: 'CS2 COMMANDS',
  help1: [
    'server             : Server status',
    'server start       : Start server',
    'server restart     : Save world and restart server',
    'server stop        : Save world and stop server',
    'auto {mode}        : Set auto mode, valid values 0,1,2,3',
    'log                : Get last 100 lines from the log',
    'players            : Show players currently online',
    'say {text}         : Send chat message to players',
    'send {line}        : Send command to server console',
    'getconfig {fileid} : Get config file as attachment',
    'setconfig {fileid} : Update config using attached file',
    'activity {query ...}    : Activity, use help for details',
    'deployment backup-world      : Backup game world to zip file',
    'deployment wipe-world-all    : Delete game world folder',
    'deployment install-runtime {version} : Install game server'
  ],
  send: '/console/help',
  getconfig: [
    'Config fileid options for download are:',
    '`cmdargs, server, gamemode-competitive, gamemode-wingman,`',
    '`gamemode-casual, gamemode-deathmatch, gamemode-custom`'
  ],
  setconfig: [
    'Config fileid options for upload are:',
    '`cmdargs, server, gamemode-competitive, gamemode-wingman,`',
    '`gamemode-casual, gamemode-deathmatch, gamemode-custom`'
  ],
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
export const say = commons.say;
export const activity = commons.activity;
