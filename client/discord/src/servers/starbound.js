import * as helptext from '../helptext.js';
import * as commons from '../commons.js';

export const startup = commons.startupAll;
export const { server, auto, log, getconfig, setconfig, deployment, players, send,
  alias, reward, trigger, activity } = commons;

export const help = helptext.newServerHelpBuilder()
  .title('STARBOUND COMMANDS')
  .addServer().addPlayers().addSend()
  .addAlias().addReward().addTrigger().addActivity()
  .addConfig(['cmdargs', 'Settings']).addDeployment()
  .build();
