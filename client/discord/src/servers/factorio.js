import * as helptext from '../helptext.js';
import * as commons from '../commons.js';

export const startup = commons.startupAll;
export const { server, auto, log, getconfig, setconfig, deployment, players, send, say,
  alias, reward, trigger, activity, chatlog } = commons;

export const help = helptext.newServerHelpBuilder()
  .title('FACTORIO COMMANDS')
  .addServer().addPlayers().addSay().addSend()
  .addAlias().addReward().addTrigger().addActivity().addChatlog()
  .next()
  .addConfig(['cmdargs', 'Server', 'Map', 'Mapgen', 'Adminlist', 'Whitelist', 'Banlist'])
  .addDeployment()
  .build();
