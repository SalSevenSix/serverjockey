const helptext = require('../helptext.js');
const commons = require('../commons.js');

const helpData = [helptext.systemHelpData, {
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
}];

export const [startup, help, server, auto, log, getconfig, setconfig, deployment, players, send, activity] = [
  commons.startAllEventLogging, helptext.help(helpData), commons.server, commons.auto, commons.log,
  commons.getconfig, commons.setconfig, commons.deployment, commons.players, commons.send, commons.activity];
