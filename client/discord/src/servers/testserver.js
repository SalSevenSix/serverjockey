import * as helptext from '../helptext.js';
import * as commons from '../commons.js';

export const startup = commons.startupAll;
export const { server, auto, log, getconfig, setconfig, deployment, players, send,
  alias, reward, trigger, activity, chatlog } = commons;

export const help = helptext.newServerHelpBuilder()
  .title('TEST SERVER COMMANDS')
  .addServer(true, true).addPlayers().addSend()
  .addAlias().addReward().addTrigger().addActivity().addChatlog()
  .addConfig(['cmdargs']).addDeployment(true)
  .build();
