export const systemHelpText = {
  title: 'SYSTEM COMMANDS',
  help1: [
    'help {command} {action}    : Show help',
    'about                      : About ServerJockey',
    'system                     : Show system information',
    'instances                  : Show server instances list',
    'use {instance}             : Switch default instance',
    'modules                    : Supported games list',
    'create {instance} {module} : Create new instance'
  ]
};

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
