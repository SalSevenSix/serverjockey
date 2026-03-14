import * as helptext from '../system/helptext.js';
import * as commons from '../system/commons.js';

export const startup = commons.startupServerOnly;
export const { status, server, auto, log, channel, panel, deployment } = commons;

export const help = helptext.newServerHelpBuilder()
  .title('TEAMSPEAK COMMANDS')
  .addServer().addChannel().addPanel()
  .addConfig(['INI', 'Allowlist', 'Denylist'])
  .addDeployment(true)
  .build();
