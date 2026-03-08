import * as helptext from '../system/helptext.js';
import * as commons from '../system/commons.js';

export const startup = commons.startupAll;
export const { status, server, auto, log, getconfig, setconfig, deployment, players, chat,
  channel, aliasme, alias, reward, trigger, activity, chatlog } = commons;

export const help = helptext.newServerHelpBuilder()
  .title('7 DAYS TO DIE COMMANDS')
  .addServer().addPlayers().addChat().addChannel().addAliasme()
  .addAlias().addReward().addTrigger().addActivity().addChatlog()
  .addConfig(['cmdargs', 'Settings', 'Admin']).addDeployment()
  .build();
