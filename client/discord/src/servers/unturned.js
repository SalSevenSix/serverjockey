import * as helptext from '../helptext.js';
import * as commons from '../commons.js';

export const startup = commons.startupAll;
export const { server, auto, log, getconfig, setconfig, deployment, players, send, say, chat,
  alias, reward, trigger, activity, chatlog } = commons;

export const help = helptext.newServerHelpBuilder()
  .title('UNTURNED COMMANDS')
  .addServer().addPlayers().addSay().addChat().addSend()
  .addAlias().addReward().addTrigger().addActivity().addChatlog()
  .next()
  .addConfig(['cmdargs', 'Commands', 'Settings', 'Workshop'])
  .addDeployment()
  .build();
