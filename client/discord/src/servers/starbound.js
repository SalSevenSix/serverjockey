import * as helptext from '../helptext.js';
import * as commons from '../commons.js';

export const startup = commons.startupAll;
export const { status, server, auto, log, getconfig, setconfig, deployment, players, send, chat,
  channel, aliasme, alias, reward, trigger, activity, chatlog } = commons;

export const help = helptext.newServerHelpBuilder()
  .title('STARBOUND COMMANDS')
  .addServer().addPlayers().addChat().addSend().addChannel()
  .addAliasme().addAlias().addReward().addTrigger().addActivity().addChatlog()
  .addConfig(['cmdargs', 'Settings']).addDeployment()
  .build();
