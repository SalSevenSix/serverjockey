import * as helptext from '../helptext.js';
import * as commons from '../commons.js';

const helpData = [helptext.systemHelpData, {
  title: 'CS2 COMMANDS',
  help1: [
    'server             : Server status',
    'server start       : Start server',
    'server restart     : Save world and restart server',
    'server stop        : Save world and stop server',
    'auto {mode}        : Set auto mode, valid values 0,1,2,3',
    'log                : Get last 100 lines from the log',
    'players            : Show players currently online',
    'alias {cmds ...}      : Alias management, use help for details',
    'reward {cmds ...}     : Reward management, use help for details',
    'trigger {cmds ...}    : Trigger management, use help for details',
    'activity {query ...}  : Activity reporting, use help for details',
    'say {text}         : Send chat message to players',
    'send {line}        : Send command to server console',
    'getconfig {fileid} : Get config file as attachment',
    'setconfig {fileid} : Update config using attached file',
    'deployment backup-world      : Backup game world to zip file',
    'deployment wipe-world-all    : Delete game world folder',
    'deployment install-runtime {version} : Install game server'
  ],
  send: '/console/help',
  alias: helptext.alias,
  reward: helptext.reward,
  trigger: helptext.trigger,
  activity: helptext.activity,
  getconfig: [
    'Config fileid options for download are:', '```',
    'cmdargs, server, gamemode-competitive, gamemode-wingman,',
    'gamemode-casual, gamemode-deathmatch, gamemode-custom', '```'
  ],
  setconfig: [
    'Config fileid options for upload are:', '```',
    'cmdargs, server, gamemode-competitive, gamemode-wingman,',
    'gamemode-casual, gamemode-deathmatch, gamemode-custom', '```'
  ]
}];

export const [startup, help, server, auto, log,
  getconfig, setconfig, deployment, players, send, say,
  alias, reward, trigger, activity] = [
  commons.startupAll, helptext.help(helpData), commons.server, commons.auto, commons.log,
  commons.getconfig, commons.setconfig, commons.deployment, commons.players, commons.send, commons.say,
  commons.alias, commons.reward, commons.trigger, commons.activity];
