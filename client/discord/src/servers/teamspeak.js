import * as helptext from '../helptext.js';
import * as commons from '../commons.js';

export const startup = commons.startupServerOnly;
export const { status, server, auto, log, deployment } = commons;

export const help = helptext.newServerHelpBuilder()
  .title('TEAMSPEAK COMMANDS')
  .addServer()
  .addConfig(['INI', 'Allowlist', 'Denylist'])
  .addDeployment(true)
  .build();
