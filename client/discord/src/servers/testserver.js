import * as helptext from '../helptext.js';
import * as commons from '../commons.js';

export const startup = commons.startupAll;
export const { status, server, auto, log, getconfig, setconfig, deployment, players, send, chat,
  alias, reward, trigger, activity, chatlog } = commons;

export const help = helptext.newServerHelpBuilder()
  .title('TEST SERVER COMMANDS')
  .addServer(true, true).addPlayers().addChat().addSend()
  .addAlias().addReward().addTrigger().addActivity().addChatlog()
  .addConfig(['cmdargs']).addDeployment(true)
  .build();
