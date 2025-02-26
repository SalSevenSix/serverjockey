import * as helptext from '../helptext.js';
import * as commons from '../commons.js';

const helpData = [helptext.systemHelpData, {
  title: 'PALWORLD COMMANDS',
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
    'deployment backup-world      : Backup game world to zip file',
    'deployment wipe-world-all    : Delete game world folder',
    'deployment wipe-world-save   : Delete only map files',
    'deployment install-runtime {version} : Install game server'
  ],
  send: '/console/help'
}];

export const [startup, help, server, auto, log, getconfig, setconfig, deployment, send] = [
  commons.startupServerOnly, helptext.help(helpData), commons.server, commons.auto, commons.log,
  commons.getconfig, commons.setconfig, commons.deployment, commons.send];

export function players($) {
  $.httptool.doPost('/console/send', { line: 'ShowPlayers' }, function(text) {
    $.message.channel.send('```\n' + text + '\n```');
  });
}
