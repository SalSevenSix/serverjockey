import * as helptext from '../helptext.js';
import * as commons from '../commons.js';

export const startup = commons.startupAll;
export const { server, auto, log, getconfig, setconfig, deployment, players, send,
  alias, reward, trigger, activity, chatlog } = commons;

export const help = helptext.newServerHelpBuilder()
  .title('STARBOUND COMMANDS')
  .addServer().addPlayers().addSend()
  .addAlias().addReward().addTrigger().addActivity().addChatlog()
  .addConfig(['cmdargs', 'Settings']).addDeployment()
  .build();
