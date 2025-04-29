import * as helptext from '../helptext.js';
import * as commons from '../commons.js';

export const startup = commons.startupAll;
export const { server, auto, log, getconfig, setconfig, deployment, players,
  alias, reward, trigger, activity, chatlog } = commons;

export const help = helptext.newServerHelpBuilder()
  .title('VALHEIM COMMANDS')
  .addServer().addPlayers()
  .addAlias().addReward().addTrigger().addActivity().addChatlog()
  .addConfig(['cmdargs', 'Adminlist', 'Permittedlist', 'Bannedlist'])
  .addDeployment()
  .build();
