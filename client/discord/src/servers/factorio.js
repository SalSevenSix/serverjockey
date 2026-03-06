import * as helptext from '../helptext.js';
import * as commons from '../commons.js';

export const startup = commons.startupAll;
export const { status, server, auto, log, getconfig, setconfig, deployment, players, send, say, chat,
  channel, aliasme, alias, reward, trigger, activity, chatlog } = commons;

export const help = helptext.newServerHelpBuilder()
  .title('FACTORIO COMMANDS')
  .addServer().addPlayers().addSay().addChat().addSend().addChannel()
  .addAliasme().addAlias().addReward().addTrigger().addActivity().addChatlog()
  .next()
  .addConfig(['cmdargs', 'Server', 'Map', 'Mapgen', 'Adminlist', 'Whitelist', 'Banlist'])
  .addDeployment()
  .build();
