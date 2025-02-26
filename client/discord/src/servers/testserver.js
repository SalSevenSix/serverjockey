import * as helptext from '../helptext.js';
import * as commons from '../commons.js';

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
    'alias {cmds ...}      : Alias management, use help for details',
    'reward {cmds ...}     : Reward management, use help for details',
    'activity {query ...}  : Activity reporting, use help for details',
    'send {line}       : Send command to server console',
    'getconfig cmdargs : Get cmd args as attachment',
    'setconfig cmdargs : Update cmd args using attached file',
    'deployment backup-runtime     : Backup server to zip file',
    'deployment install-runtime {version} : Install game server'
  ],
  send: '/console/help',
  alias: helptext.alias,
  reward: helptext.reward,
  activity: helptext.activity
}];

export const [startup, help, server, auto, log,
  getconfig, setconfig, deployment, players, send,
  alias, reward, activity] = [
  commons.startupAll, helptext.help(helpData), commons.server, commons.auto, commons.log,
  commons.getconfig, commons.setconfig, commons.deployment, commons.players, commons.send,
  commons.alias, commons.reward, commons.activity];
