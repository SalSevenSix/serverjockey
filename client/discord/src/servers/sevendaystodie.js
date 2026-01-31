import * as helptext from '../helptext.js';
import * as commons from '../commons.js';

export const startup = commons.startupAll;
export const { status, server, auto, log, getconfig, setconfig, deployment, players, chat,
  aliasme, alias, reward, trigger, activity, chatlog } = commons;

export const help = helptext.newServerHelpBuilder()
  .title('7 DAYS TO DIE COMMANDS')
  .addServer().addPlayers().addChat().addAliasme()
  .addAlias().addReward().addTrigger().addActivity().addChatlog()
  .addConfig(['cmdargs', 'Settings', 'Admin']).addDeployment()
  .build();
