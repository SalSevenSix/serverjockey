import * as cutil from 'common/util/util';

function processSection(context, httptool, message, data, section) {
  const cmd = context.config.CMD_PREFIX;
  if (data.length === 0) {
    let [index, header] = [1, '```\n'];
    if (section.title) { header += section.title + '\n'; }
    header += cmd;
    while (cutil.hasProp(section, 'help' + index)) {
      message.channel.send(header + section['help' + index].join('\n' + cmd) + '\n```');
      if (index === 1) { header = '```\n' + cmd; }
      index += 1;
    }
    return null;
  }
  const query = data.join('-');
  if (query === 'title' || !cutil.hasProp(section, query)) return false;
  if (cutil.isString(section[query])) {
    httptool.doGet(section[query], function(body) { return '```\n' + body + '\n```'; });
  } else {
    message.channel.send(section[query].map(function(line) {
      return line && line.slice(0, 2) === '`!' ? '`' + cmd + line.slice(2) : line;
    }).join('\n'));
  }
  return true;
}

function processData(context, httptool, message, data, helpData) {
  const sections = Array.isArray(helpData) ? helpData : [helpData];
  let [index, done] = [0, false];
  while (index < sections.length && !done) {
    done = processSection(context, httptool, message, data, sections[index]);
    index += 1;
  }
  if (done === false) {
    message.channel.send('No more help available.');
  }
}

function process(helpData) {
  return function($) { processData($.context, $.httptool, $.message, $.data, helpData); };
}

function newHelpBuilder() {
  const [self, data] = [{}, {}];
  let paragraph = 0;

  const current = function() { return 'help' + paragraph; };

  self.title = function(value) {
    data.title = value;
    return self;
  };

  self.next = function() {
    paragraph += 1;
    data[current()] = [];
    return self;
  };

  self.add = function(value) {
    if (Array.isArray(value)) { data[current()].push(...value); }
    else { data[current()].push(value); }
    return self;
  };

  self.addHelp = function(command, value) {
    let indexes = [command.indexOf('"'), command.indexOf('{'), command.indexOf(':')];
    indexes = indexes.filter(function(index) { return index > -1; });
    if (indexes.length === 0) { indexes.push(-1); }
    const index = indexes.reduce(function(a, b) { return a > b ? b : a; });
    let key = command;
    if (index > -1) { key = key.slice(0, index); }
    key = key.trim().replaceAll(' ', '-');
    data[key] = value;
    return self;
  };

  self.buildData = function() { return { ...data }; };
  return self.next();
}

const systemHelpData = newHelpBuilder()
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
    'Show help text. Use {command} and {action} for more detailed information. Both optional.'
  ])
  .buildData();

export const systemHelp = function() { return process(systemHelpData); };

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
  'TODO',
  'TODO'];

const playersHelp = 'players            : Show players currently online';

const sayHelp = 'say {text}         : Send chat message to players';

const sendHelp = 'send {line}        : Send command to server console';
const helpSend = '/console/help';

const deploymentHelp = [
  'deployment backup-world {hours} : Backup game world to zip file',
  'deployment wipe-world-save      : Delete only map files',
  'deployment wipe-world-all       : Delete game world folder',
  'deployment install-runtime {version} : Install game server'];
const helpDeploymentBackupWorld = [
  'Make a backup of the game world to a zip file.',
  'Optionally specify {hours} to prune backups older than hours.',
  'Log output will be attached as a file.'];
const helpDeploymentInstallRuntime = [
  'Install game server, {version} optional.',
  'For Steam installs, use the beta for version.',
  'Log output will be attached as a file.'];

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
  '  rq-role={roleid}        : Player must have this role for action',
  '  rq-not-role={roleid}    : Player must not have this role for action',
  '  cx-channel={channelid}  : Channel to use for any actions',
  '  cx-delay={seconds}      : Delay between trigger event and actions',
  '  do-add-role={roleid}    : Action add role to player',
  '  do-remove-role={roleid} : Action remove role from player',
  '  "do-message={line}"     : Action send message, can be command with subs;',
  '  {!} for command prefix, {instance} for instance, {player} for "name"',
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

/* eslint-disable max-lines-per-function */
export function newServerHelpBuilder() {
  const builder = newHelpBuilder();
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
  self.addSay = function() { return self.add(sayHelp); };
  self.addSend = function() { return self.addHelp(sendHelp, helpSend).add(sendHelp); };
  self.addAlias = function() { return self.addHelp(aliasHelp, helpAlias).add(aliasHelp); };
  self.addReward = function() { return self.addHelp(rewardHelp, helpReward).add(rewardHelp); };
  self.addTrigger = function() { return self.addHelp(triggerHelp, helpTrigger).add(triggerHelp); };
  self.addActivity = function() { return self.addHelp(activityHelp, helpActivity).add(activityHelp); };

  self.build = function() { return process([systemHelpData, builder.buildData()]); };
  return self;
}
/* eslint-enable max-lines-per-function */
