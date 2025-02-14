const cutil = require('common/util/util');

export const systemHelpData = {
  title: 'SYSTEM COMMANDS',
  help1: [
    'help {command} {action}    : Show help',
    'about                      : About ServerJockey',
    'system                     : Show system information',
    'instances                  : Show server instances list',
    'use {instance}             : Switch default instance',
    'modules                    : Supported games list',
    'create {instance} {module} : Create new instance'
  ],
  help: [
    'Show help text. Use {command} and {action} for more detailed information. Both optional.'
  ]
};

export const alias = [
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
  '`!alias remove @RealMrTee`'
];

export const reward = [
  'Reward Management. Give players roles for achievements. Commands are...', '```',
  'list           : List all rewards for the instance (default command)',
  'add            : Add reward scheme, with following parameters...',
  '  give|take    : Give or take role based on >= or < than threshold',
  '  {roleid}     : The @ID of the reward role',
  '  played|top   : Choose to reward based on time played or ranking',
  '  {threshold}  : Threshold to check for reward evaluation',
  '  {range}      : Time range for player activity query',
  'remove {id}    : Remove reward by id as shown in list',
  'evaluate       : Process players and allocate reward roles',
  '```', 'Examples...',
  'a) Give @HighAchiever role if ranked top 3 player in last 7 days',
  '`!reward add give @HighAchiever top 3 7d`',
  'a) Give @Battler role if played more than 5 hours in last 7 days',
  '`!reward add give @Battler played 5h 7d`',
  'a) Take away @Battler role if played less than 1 hour in last 30 days',
  '`!reward add take @Battler played 1h 30d`'
];

export const activity = [
  'Activity Reporting. Provide the following query parameters...', '```',
  'instance        : Report instance activity instead of player activity',
  'from={date}     : From date in ISO 8601 format YYYY-MM-DDThh:mm:ss',
  '                  or days {n}D prior, or hours {n}H prior to date',
  'to={date}       : To date in ISO 8601 format YYYY-MM-DDThh:mm:ss',
  '                  or preset "LD" Last Day, "LM" Last Month, "TD" This Month',
  'tz={timezone}   : Timezone as ±{hh} or ±{hh}:{mm} default is server tz',
  '"player={name}" : Specify a player by name to report on',
  'limit={rows}    : Limit number of players rows returned',
  'format={type}   : Provide results in "TEXT" or "JSON" format',
  '```', 'Examples...',
  'a) get instance activity between specific dates in timezone GMT +7',
  '`!activity instance from=2024-08-01T00:00:00 to=2024-09-01T00:00:00 tz=+7`',
  'b) get the top 3 players from last 7 days ending yesterday',
  '`!activity from=7D to=LD limit=4`',
  'c) get player activity by name in json format',
  '`!activity "player=Mr Tee" format=JSON`'
];

function sendHelpSection(context, httptool, message, data, section) {
  const cmd = context.config.CMD_PREFIX;
  if (data.length === 0) {
    let header = '```\n' + section.title + '\n' + cmd;
    let index = 1;
    while (cutil.hasProp(section, 'help' + index)) {
      message.channel.send(header + section['help' + index].join('\n' + cmd) + '\n```');
      if (index === 1) { header = '```\n' + cmd; }
      index += 1;
    }
    return null;
  }
  const query = data.join('').replaceAll('-', '');
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

function sendHelpData(context, httptool, message, data, helpData) {
  const sections = Array.isArray(helpData) ? helpData : [helpData];
  let [index, done] = [0, false];
  while (index < sections.length && !done) {
    done = sendHelpSection(context, httptool, message, data, sections[index]);
    index += 1;
  }
  if (done === false) {
    message.channel.send('No more help available.');
  }
}

export function help(helpData) {
  return function($) { sendHelpData($.context, $.httptool, $.message, $.data, helpData); };
}
