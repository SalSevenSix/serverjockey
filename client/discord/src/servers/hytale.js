import * as helptext from '../helptext.js';
import * as commons from '../commons.js';

export const startup = commons.startupAll;
export const { status, server, auto, log, getconfig, setconfig, players, send, say, chat,
  aliasme, alias, reward, trigger, activity, chatlog } = commons;

export const help = helptext.newServerHelpBuilder()
  .title('HYTALE COMMANDS')
  .addServer().addPlayers().addSay().addChat().addSend().addAliasme()
  .addAlias().addReward().addTrigger().addActivity().addChatlog()
  .next()
  .addConfig(['cmdargs', 'Mods', 'Settings', 'Permissions', 'Whitelist', 'Bans', 'Memories', 'Warps'])
  .build();
