import * as msgutil from '../util/msgutil.js';
import * as helptext from '../helptext.js';
import * as commons from '../commons.js';

export const startup = commons.startupServerOnly;
export const { status, server, auto, log, getconfig, setconfig, deployment, chat, send } = commons;

export const help = helptext.newServerHelpBuilder()
  .title('PALWORLD COMMANDS')
  .addServer().addPlayers().addChat().addSend()
  .addConfig(['cmdargs', 'Settings']).addDeployment()
  .build();

export function players({ httptool, message }) {
  httptool.doPost('/console/send', { line: 'ShowPlayers' }, function(text) {
    msgutil.sendText(message, text ? text : 'No players online');
  });
}
