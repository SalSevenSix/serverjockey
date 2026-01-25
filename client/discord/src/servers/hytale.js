import * as helptext from '../helptext.js';
import * as commons from '../commons.js';

export const startup = commons.startupAll;
export const { status, server, auto, log, getconfig, setconfig, players, send, say, chat,
  alias, reward, trigger, activity, chatlog } = commons;

export const help = helptext.newServerHelpBuilder()
  .title('HYTALE COMMANDS')
  .addServer().addPlayers().addSay().addChat().addSend()
  .addAlias().addReward().addTrigger().addActivity().addChatlog()
  .next()
  .addConfig(['cmdargs', 'Config', 'Permissions', 'Whitelist', 'Bans', 'Default'])
  .build();
