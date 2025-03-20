import * as helptext from '../helptext.js';
import * as commons from '../commons.js';

export const startup = commons.startupAll;
export const { server, auto, log, getconfig, setconfig, deployment, players, send, say,
  alias, reward, trigger, activity } = commons;

export const help = helptext.newServerHelpBuilder()
  .title('UNTURNED COMMANDS')
  .addServer().addPlayers().addSay().addSend()
  .addAlias().addReward().addTrigger().addActivity()
  .next()
  .addConfig(['cmdargs', 'Commands', 'Settings', 'Workshop'])
  .addDeployment()
  .build();
