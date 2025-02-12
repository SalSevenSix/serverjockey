const helptext = require('../helptext.js');
const commons = require('../commons.js');

const helpData = [helptext.systemHelpData, {
  title: 'STARBOUND COMMANDS',
  help1: [
    'server             : Server status',
    'server start       : Start server',
    'server restart     : Save world and restart server',
    'server stop        : Save world and stop server',
    'auto {mode}        : Set auto mode, valid values 0,1,2,3',
    'log                : Get last 100 lines from the log',
    'players            : Show players currently online',
    'alias {cmds ...}      : Alias management, use help for details',
    'activity {query ...}  : Activity reporting, use help for details',
    'send {line}        : Send command to server console',
    'getconfig cmdargs  : Get launch options as attachment',
    'getconfig settings : Get settings as attachment',
    'setconfig cmdargs  : Update launch options using attached file',
    'setconfig settings : Update settings using attached file',
    'deployment backup-world      : Backup game world to zip file',
    'deployment wipe-world-all    : Delete game world folder',
    'deployment wipe-world-save   : Delete only map files',
    'deployment install-runtime {beta} : Install game server'
  ],
  send: '/console/help',
  alias: helptext.alias,
  activity: helptext.activity
}];

export const [startup, help, server, auto, log,
  getconfig, setconfig, deployment, players, send,
  activity, alias] = [
  commons.startAllEventLogging, helptext.help(helpData), commons.server, commons.auto, commons.log,
  commons.getconfig, commons.setconfig, commons.deployment, commons.players, commons.send,
  commons.activity, commons.alias];
