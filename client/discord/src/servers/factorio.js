import * as helptext from '../system/helptext.js';
import * as commons from '../system/commons.js';

export const startup = commons.startupAll;
export const { status, server, auto, log, getconfig, setconfig, deployment, players, send, say, chat,
  channel, panel, aliasme, alias, reward, trigger, activity, chatlog } = commons;

export const help = helptext.newServerHelpBuilder()
  .title('FACTORIO COMMANDS')
  .addServer().addPlayers().addSay().addChat().addSend().addChannel().addPanel()
  .addAliasme().addAlias().addReward().addTrigger().addActivity().addChatlog()
  .next()
  .addConfig(['cmdargs', 'Server', 'Map', 'Mapgen', 'Adminlist', 'Whitelist', 'Banlist'])
  .addDeployment()
  .build();
