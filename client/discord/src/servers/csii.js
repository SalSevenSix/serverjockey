import * as helptext from '../helptext.js';
import * as commons from '../commons.js';

export const startup = commons.startupAll;
export const { server, auto, log, getconfig, setconfig, deployment, players, send, say,
  alias, reward, trigger, activity } = commons;

export const help = helptext.newServerHelpBuilder()
  .title('CS2 COMMANDS')
  .addServer().addPlayers().addSay().addSend()
  .addAlias().addReward().addTrigger().addActivity()
  .addConfig().addDeployment(true)
  .addHelp('getconfig', [
    'Config fileid options for download are:', '```',
    'cmdargs, server, gamemode-competitive, gamemode-wingman,',
    'gamemode-casual, gamemode-deathmatch, gamemode-custom', '```'])
  .addHelp('setconfig', [
    'Config fileid options for upload are:', '```',
    'cmdargs, server, gamemode-competitive, gamemode-wingman,',
    'gamemode-casual, gamemode-deathmatch, gamemode-custom', '```'])
  .build();
