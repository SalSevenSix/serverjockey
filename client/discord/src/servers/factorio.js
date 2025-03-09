import * as helptext from '../helptext.js';
import * as commons from '../commons.js';

const helpData = [helptext.systemHelpData, {
  title: 'FACTORIO COMMANDS',
  help1: [
    'server            : Server status',
    'server start      : Start server',
    'server restart    : Save world and restart server',
    'server stop       : Save world and stop server',
    'auto {mode}       : Set auto mode, valid values 0,1,2,3',
    'log               : Get last 100 lines from the log',
    'players           : Show players currently online',
    'alias {cmds ...}      : Alias management, use help for details',
    'reward {cmds ...}     : Reward management, use help for details',
    'trigger {cmds ...}    : Trigger management, use help for details',
    'activity {query ...}  : Activity reporting, use help for details',
    'say {text}        : Send chat message to players',
    'send {line}       : Send command to server console'
  ],
  help2: [
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
    'deployment backup-world      : Backup game world to zip file',
    'deployment wipe-world-all    : Delete game world folder',
    'deployment wipe-world-config : Delete only config files',
    'deployment wipe-world-save   : Delete only map file',
    'deployment install-runtime {version} : Install game server'
  ],
  send: '/console/help',
  alias: helptext.alias,
  reward: helptext.reward,
  trigger: helptext.trigger,
  activity: helptext.activity
}];

export const [startup, help, server, auto, log,
  getconfig, setconfig, deployment, players, send, say,
  alias, reward, trigger, activity] = [
  commons.startupAll, helptext.help(helpData), commons.server, commons.auto, commons.log,
  commons.getconfig, commons.setconfig, commons.deployment, commons.players, commons.send, commons.say,
  commons.alias, commons.reward, commons.trigger, commons.activity];
