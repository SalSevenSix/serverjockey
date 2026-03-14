import * as helptext from '../system/helptext.js';
import * as commons from '../system/commons.js';

export const startup = commons.startupAll;
export const { status, server, auto, log, getconfig, setconfig, deployment, players, chat,
  channel, panel, aliasme, alias, reward, trigger, activity } = commons;

export const help = helptext.newServerHelpBuilder()
  .title('VALHEIM COMMANDS')
  .addServer().addPlayers().addChat().addChannel().addPanel()
  .addAliasme().addAlias().addReward().addTrigger().addActivity()
  .next()
  .addConfig(['cmdargs', 'Adminlist', 'Permittedlist', 'Bannedlist'])
  .addDeployment()
  .build();
