import * as helptext from '../system/helptext.js';
import * as commons from '../system/commons.js';

export const startup = commons.startupAll;
export const { status, server, auto, log, getconfig, setconfig, deployment, players, send, chat,
  channel, aliasme, alias, reward, trigger, activity, chatlog } = commons;

export const help = helptext.newServerHelpBuilder()
  .title('TEST SERVER COMMANDS')
  .addServer(true, true).addPlayers().addChat().addSend().addChannel()
  .addAliasme().addAlias().addReward().addTrigger().addActivity().addChatlog()
  .addConfig(['cmdargs']).addDeployment(true)
  .build();
