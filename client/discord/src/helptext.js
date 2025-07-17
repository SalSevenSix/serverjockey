import * as help from './util/help.js';

const systemHelpData = help.newHelpBuilder()
  .title('SYSTEM COMMANDS')
  .add([
    'help {command} {action}    : Show help',
    'about                      : About ServerJockey',
    'system                     : Show system information',
    'instances                  : Show server instances list',
    'use {instance}             : Switch default instance',
    'modules                    : Supported games list',
    'create {instance} {module} : Create new instance'])
  .addHelp('help', [
    'Show help text. Use {command} and {action} for more detailed information. Both optional.',
    'e.g. `!help create` to show more help on the create command.'])
  .addHelp('use', [
    'Set the default {instance} for commands to be directed to.',
    'If {instance} not provided, the current default instance is shown.',
    'Alternatively, commands can be directed to any instance explicitly',
    'by using the notation {instance}.{command} in place of the command...',
    'e.g. `!myserver.server start`'])
  .addHelp('create', [
    'Create a new instance named {instance} for game {module}.',
    'e.g. `!create myserver projectzomboid`',
    'Use the `!modules` command to see the list of available games.'])
  .buildData();

export const systemHelp = help.process(systemHelpData);

const serverHelp = [
  'server             : Server status',
  'server start       : Start server',
  'server restart     : Save world and restart server',
  'server restart-after-warnings : Warnings then restart server',
  'server restart-on-empty       : Restart when server is empty',
  'server stop        : Save world and stop server',
  'auto {mode}        : Set auto mode, valid values 0,1,2,3',
  'log                : Get last 100 lines from the log'];
const helpServerAuto = [
  'Show the current auto mode if {mode} not provided.',
  'Set auto behaviour with {mode} option...', '```',
  '0 : No automatic actions',
  '1 : Automatically start the game server when ServerJockey starts',
  '2 : Automatically restart the game server if it crashes',
  '3 : Both automatic Start and Restart actions', '```'];

const playersHelp = 'players            : Show players currently online';

const sayHelp = 'say {text}         : Send a message to players in-game';
const helpSay = [
  'Send a text message from discord to players in the game. e.g.',
  '`!say Hello everyone, will be playing soon`'];

const sendHelp = 'send {line}        : Send command to server console';
const helpSend = '/console/help';

const chatHelp = 'chat {text}        : Chat with the AI game assistant';
const helpChat = [
  'Game context aware chatbot assistant powered by AI. e.g.',
  '`!chat Tell me a joke about the game.`',
  'Also works in-game if `!say` is supported, just ask using command key. e.g.',
  '`! I just started playing, what should I do first?`',
  'Conversations will be remembered for up to 7 minutes.',
  'Manually reset the conversation by using the command without any text.'];

const deploymentHelp = [
  'deployment backup-world {hours} : Backup game world to zip file',
  'deployment wipe-world-save      : Delete only game save files',
  'deployment wipe-world-all       : Delete game world folder',
  'deployment install-runtime {version} : Install game server'];
const helpDeploymentBackupWorld = [
  'Make a backup of the game world to a zip file.',
  'Optionally specify {hours} to prune backups older than hours.',
  'Log output will be attached as a file.'];
const helpDeploymentInstallRuntime = [
  'Install game server, {version} is optional.',
  'For Steam installs, use the beta for version.',
  'Console output will be attached as a file.'];

const aliasHelp = 'alias {cmds ...}     : Alias management, use help for details';
const helpAlias = [
  'Alias Management. Link discord users to player names. Commands are...', '```',
  'list              : List all aliases for the instance (default command)',
  'find {alias}      : Find an alias by @ID, snowflake, discordid, player name',
  'add {id} "{name}" : Add alias linking id as @ID or snowflake to player name',
  'remove {id}       : Remove alias by @ID, snowflake, discordid',
  '```', 'Examples...',
  'a) add alias linking discord user @RealMrTee to player name "Mr Tee"',
  '`!alias add @RealMrTee "Mr Tee"`',
  'b) find alias for discord user @RealMrTee',
  '`!alias find @RealMrTee`',
  'c) find alias for player name "Mr Tee"',
  '`!alias find "Mr Tee"`',
  'd) remove alias for discord user @RealMrTee',
  '`!alias remove @RealMrTee`'];

const rewardHelp = 'reward {cmds ...}    : Reward management, use help for details';
const helpReward = [
  'Reward Management. Give players roles for achievements. Commands are...', '```',
  'list           : List all rewards for the instance (default command)',
  'add            : Add reward scheme, with following parameters...',
  '  give|take    : Give or take role based on >= or < than threshold',
  '  {roleid}     : The @ID or snowflake of the reward role',
  '  played|top   : Choose to reward based on time played or ranking',
  '  {threshold}  : Threshold to evaluate, negative value to invert',
  '  {range}      : Time range for player activity query',
  'move {id} {±#} : Move reward by id up or down list',
  'remove {id}    : Remove reward by id as shown in list',
  'evaluate       : Process players and allocate reward roles',
  '```', 'Examples...',
  'a) Give @HighAchiever role if ranked top 3 player in last 7 days',
  '`!reward add give @HighAchiever top 3 7d`',
  'b) Give @Battler role if played more than 5 hours in last 7 days',
  '`!reward add give @Battler played 5h 7d`',
  'c) Take away @Battler role if played less than 1 hour in last 30 days',
  '`!reward add take @Battler played 1h 30d`',
  'd) Take away @Slacker role if played more than 7 hours in last 14 days',
  '`!reward add take @Slacker played -7h 14d`'];

const triggerHelp = 'trigger {cmds ...}   : Trigger management, use help for details';
const helpTrigger = [
  'Trigger Management. Trigger actions on player events. Commands are...', '```',
  'list           : List all triggers for the instance (default command)',
  'add            : Add trigger with following parameters...',
  '  on-login                : Trigger on player login',
  '  on-logout               : Trigger on player logout',
  '  on-death                : Trigger on player death',
  '  on-started              : Trigger on server started',
  '  on-stopped              : Trigger on server stopped',
  '  rq-role={roleid}        : Player must have this role for action',
  '  rq-not-role={roleid}    : Player must not have this role for action',
  '  cx-channel={channelid}  : Channel to use for any actions',
  '  cx-delay={seconds}      : Delay between trigger event and actions',
  '  do-add-role={roleid}    : Action add role to player',
  '  do-remove-role={roleid} : Action remove role from player',
  '  "do-message={line}"     : Action send message, can be command with subs;',
  '    {!} for command prefix, {instance} for instance, {player} for "name"',
  'remove {id}    : Remove trigger by id as shown in list',
  '```', 'Examples...',
  'a) Give PZ player an Axe on login if has @AxemanKit role, also remove role',
  '```', '!trigger add on-login rq-role=@AxemanKit do-remove-role=@AxemanKit',
  '"do-message={!}{instance}.player {player} give-item Base Axe"', '```',
  'b) Give @Zombie role to player on death and announce it on #general channel',
  '```', '!trigger add on-death cx-channel=#general',
  'do-add-role=@Zombie "do-message={member} Died!"', '```'];

const activityHelp = 'activity {query ...} : Activity reporting, use help for details';
const helpActivity = [
  'Activity Reporting. Provide the following query parameters...', '```',
  'instance        : Report instance activity instead of player activity',
  'from={date}     : From date in ISO 8601 format YYYY-MM-DDThh:mm:ss',
  '                  or days {#}d prior, or hours {#}h prior to date',
  'to={date}       : To date in ISO 8601 format YYYY-MM-DDThh:mm:ss',
  '                  or preset "LD" Last Day, "LM" Last Month, "TD" This Month',
  'tz={timezone}   : Timezone as ±{hh} or ±{hh}:{mm} default is server tz',
  '"player={name}" : Specify a player by name to report on',
  'limit={rows}    : Limit number of player rows returned',
  'format={type}   : Provide results in "TEXT" or "JSON" format',
  '```', 'Examples...',
  'a) get instance activity between specific dates in timezone GMT +7',
  '`!activity instance from=2024-08-01T00:00:00 to=2024-09-01T00:00:00 tz=+7`',
  'b) get the top 3 players from last 7 days ending yesterday',
  '`!activity from=7d to=LD limit=4`',
  'c) get player activity by name in json format',
  '`!activity "player=Mr Tee" format=JSON`'];

const chatlogHelp = 'chatlog {query ...}  : Chat Log queries, use help for details';
const helpChatlog = [
  'Chat Log Queries. Provide the following query parameters...', '```',
  'from={date}     : From date in ISO 8601 format YYYY-MM-DDThh:mm:ss',
  '                  or hours {#}h prior, or minutes {#}m prior to date',
  'to={date}       : To date in ISO 8601 format YYYY-MM-DDThh:mm:ss',
  '                  or preset "LH" Last Hour, "LD" Last Day',
  'tz={timezone}   : Timezone as ±{hh} or ±{hh}:{mm} default is server tz',
  '"player={name}" : Only chat messages for player by name',
  'summary         : Summarize chat results (requires AI configuration)',
  '```', 'Examples...',
  'a) get chat messages between specific times in timezone GMT +7',
  '`!chatlog from=2024-08-15T09:00:00 to=2024-08-15T21:00:00 tz=+7`',
  'b) get chat messages from last 12 hours to end of last hour',
  '`!chatlog from=12h to=LH`',
  'c) generate a summary of the chat messages from the last 24 hours',
  '`!chatlog from=24h summary`'];

/* eslint-disable max-lines-per-function */
export function newServerHelpBuilder() {
  const builder = help.newHelpBuilder();
  const self = {};

  self.title = function(value) {
    builder.title(value);
    return self;
  };

  self.next = function() {
    builder.next();
    return self;
  };

  self.add = function(value) {
    builder.add(value);
    return self;
  };

  self.addHelp = function(command, value) {
    builder.addHelp(command, value);
    return self;
  };

  self.addServer = function(restartWarnings = false, restartEmpty = false) {
    self.addHelp(serverHelp[6], helpServerAuto);
    const result = [...serverHelp.slice(0, 3)];
    if (restartWarnings) { result.push(serverHelp[3]); }
    if (restartEmpty) { result.push(serverHelp[4]); }
    result.push(...serverHelp.slice(-3));
    return self.add(result);
  };

  self.addConfig = function(values = null) {
    const [result, configMap] = [[], {}];
    if (values && values.length > 0) {
      values.forEach(function(value) {
        const index = value.indexOf(' ');
        const key = index === -1 ? value : value.slice(0, index);
        configMap[key.toLowerCase()] = value === 'cmdargs' ? 'Launch' : value;
      });
    } else {
      configMap['{fileid}'] = 'fileid';
    }
    const pad = 1 + Object.keys(configMap).reduce(function(a, b) { return a.length > b.length ? a : b; }).length;
    for (const [key, value] of Object.entries(configMap)) {
      result.push('getconfig ' + key.padEnd(pad) + ': Get ' + value + ' config as attachment');
    }
    for (const [key, value] of Object.entries(configMap)) {
      result.push('setconfig ' + key.padEnd(pad) + ': Update ' + value + ' using attached file');
    }
    return self.add(result);
  };

  self.addDeployment = function(noWorld = false) {
    self.addHelp(deploymentHelp[0], helpDeploymentBackupWorld);
    self.addHelp(deploymentHelp[3], helpDeploymentInstallRuntime);
    const result = [deploymentHelp[0]];
    if (!noWorld) { result.push(deploymentHelp[1]); }
    result.push(...deploymentHelp.slice(-2));
    return self.add(result);
  };

  self.addPlayers = function() { return self.add(playersHelp); };
  self.addSay = function() { return self.addHelp(sayHelp, helpSay).add(sayHelp); };
  self.addSend = function() { return self.addHelp(sendHelp, helpSend).add(sendHelp); };
  self.addChat = function() { return self.addHelp(chatHelp, helpChat).add(chatHelp); };
  self.addAlias = function() { return self.addHelp(aliasHelp, helpAlias).add(aliasHelp); };
  self.addReward = function() { return self.addHelp(rewardHelp, helpReward).add(rewardHelp); };
  self.addTrigger = function() { return self.addHelp(triggerHelp, helpTrigger).add(triggerHelp); };
  self.addActivity = function() { return self.addHelp(activityHelp, helpActivity).add(activityHelp); };
  self.addChatlog = function() { return self.addHelp(chatlogHelp, helpChatlog).add(chatlogHelp); };

  self.build = function() { return help.process([systemHelpData, builder.buildData()]); };
  return self;
}
/* eslint-enable max-lines-per-function */
