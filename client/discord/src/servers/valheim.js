import * as helptext from '../helptext.js';
import * as commons from '../commons.js';

export const startup = commons.startupAll;
export const { status, server, auto, log, getconfig, setconfig, deployment, players, chat,
  channel, aliasme, alias, reward, trigger, activity } = commons;

export const help = helptext.newServerHelpBuilder()
  .title('VALHEIM COMMANDS')
  .addServer().addPlayers().addChat().addChannel()
  .addAliasme().addAlias().addReward().addTrigger().addActivity()
  .next()
  .addConfig(['cmdargs', 'Adminlist', 'Permittedlist', 'Bannedlist'])
  .addDeployment()
  .build();
