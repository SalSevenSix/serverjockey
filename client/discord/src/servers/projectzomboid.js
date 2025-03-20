import * as cutil from 'common/util/util';
import * as util from '../util/util.js';
import * as logger from '../util/logger.js';
import * as helptext from '../helptext.js';
import * as commons from '../commons.js';

const helpData = [helptext.systemHelpData, {
  title: 'PROJECT ZOMBOID COMMANDS',
  help1: [
    'server                    : Server status',
    'server start              : Start server',
    'server restart            : Save world and restart server',
    'server restart-after-warnings : Warnings then restart server',
    'server restart-on-empty       : Restart when server is empty',
    'server stop               : Save world and stop server',
    'auto {mode}               : Set auto mode, valid values 0,1,2,3',
    'log                       : Get last 100 lines from the log',
    'alias {cmds ...}          : Alias management, use help for details',
    'reward {cmds ...}         : Reward management, use help for details',
    'trigger {cmds ...}        : Trigger management, use help for details',
    'activity {query ...}      : Activity reporting, use help for details',
    'world save                : Save the game world',
    'world broadcast {message} : Broadcast message to all players',
    'world chopper             : Trigger chopper event',
    'world gunshot             : Trigger gunshot event',
    'world start-storm         : Start a storm',
    'world stop-weather        : Stop current weather',
    'world start-rain          : Start rain',
    'world stop-rain           : Stop rain'
  ],
  help2: [
    'players                   : Show players currently online',
    'player "{name}" kick      : Kick from server',
    'player "{name}" set-access-level {level} : Set access level',
    'player "{name}" tele-to "{toplayer}"     : Teleport to player',
    'player "{name}" tele-at {x,y,z}          : Teleport to location',
    'player "{name}" give-xp {skill} {xp}     : Give XP',
    'player "{name}" give-item {module} {item} {count} : Give item',
    'player "{name}" spawn-vehicle {module} {item} : Spawn vehicle',
    'player "{name}" spawn-horde {count}      : Spawn zombies',
    'player "{name}" lightning                : Trigger lightning',
    'player "{name}" thunder                  : Trigger thunder',
    'whitelist add-name "{name}" "{pwd}" : Add player by name',
    'whitelist remove-name "{name}"      : Remove player by name',
    'whitelist add-id {id} "{name}" : Add player by @ID, name or alias req',
    'whitelist remove-id {id}       : Remove player by @ID, alias required',
    'whitelist reset-password {id}  : experimental, alias required',
    'banlist add {steamid}          : Add player SteamID to banlist',
    'banlist remove {steamid}       : Remove player SteamID from banlist'
  ],
  help3: [
    'getconfig cmdargs      : Get launch options as attachment',
    'getconfig ini          : Get INI config as attachment',
    'getconfig sandbox      : Get Sandbox config as attachment',
    'getconfig spawnregions : Get Spawnregions config as attachment',
    'getconfig spawnpoints  : Get Spawnpoints config as attachment',
    'getconfig jvm          : Get JVM config as attachment',
    'setconfig cmdargs      : Update launch options using attached file',
    'setconfig ini          : Update INI using attached file',
    'setconfig sandbox      : Update Sandbox using attached file',
    'setconfig spawnregions : Update Spawnregions using attached file',
    'setconfig spawnpoints  : Update Spawnpoints using attached file',
    'setconfig jvm          : Update JVM config using attached file',
    'deployment backup-world {hours}   : Backup game world to zip file',
    'deployment wipe-world-save        : Delete only map files',
    'deployment wipe-world-all         : Delete game world folder',
    'deployment install-runtime {beta} : Install game server'
  ],
  alias: helptext.alias,
  reward: helptext.reward,
  trigger: helptext.trigger,
  activity: helptext.activity,
  playersetaccesslevel: [
    'Set access level for online player. Level options:', '```',
    'admin, moderator, overseer, gm, observer, none', '```'
  ],
  playergivexp: [
    'Give XP to online player. Skill options:', '```',
    'Sprinting, Lightfoot, Nimble, Sneak, Aiming, Reloading,',
    'Axe, SmallBlunt, Blunt, Spear, SmallBlade, LongBlade, Combat,',
    'Woodwork, Cooking, Farming, Doctor, Electricity, MetalWelding,',
    'Tailoring, Mechanics, FlintKnapping, Carving, Masonry, Pottery,',
    'Fishing, Trapping, PlantScavenging, Fitness, Strength', '```'
  ],
  playergiveitem: [
    'Give item to player, {count} is optional.'
  ],
  playerspawnvehicle: [
    'Spawn a vehicle next to player. Condition will vary.'
  ],
  deploymentbackupworld: [
    'Make a backup of the game world to a zip file.',
    'Optionally specify {hours} to prune backups older than hours.',
    'Log output will be attached as a file.'
  ],
  deploymentinstallruntime: [
    'Install game server, {beta} optional.',
    'Log output will be attached as a file.'
  ]
}];

export const [startup, help] = [commons.startupAll, helptext.help(helpData)];
export const { server, auto, log, getconfig, setconfig, deployment, players,
  alias, reward, trigger, activity } = commons;

export function world($) {
  const [httptool, message, data] = [$.httptool, $.message, [...$.data]];
  if (data.length === 0) return util.reactUnknown(message);
  const cmd = data.shift();
  let body = null;
  if (cmd === 'broadcast') {
    if (data.length === 0) return util.reactUnknown(message);
    body = { message: data.join(' ') };
  }
  httptool.doPost('/world/' + cmd, body);
}

export function player($) {
  const [httptool, aliases, message, data] = [$.httptool, $.aliases, $.message, [...$.data]];
  if (data.length < 2) return util.reactUnknown(message);
  let name = data.shift();
  const cmd = data.shift();
  let body = null;
  if (data.length > 0) {
    if (cmd === 'set-access-level') {
      body = { level: data[0] };
    } else if (cmd === 'tele-to') {
      body = { toplayer: data[0] };
    } else if (cmd === 'tele-at') {
      body = { location: data[0] };
    } else if (cmd === 'spawn-horde') {
      body = { count: data[0] };
    } else if (cmd === 'spawn-vehicle') {
      if (data.length < 2) return util.reactUnknown(message);
      body = { module: data[0], item: data[1] };
    } else if (cmd === 'give-xp') {
      if (data.length < 2) return util.reactUnknown(message);
      body = { skill: data[0], xp: data[1] };
    } else if (cmd === 'give-item') {
      if (data.length < 2) return util.reactUnknown(message);
      body = { module: data[0], item: data[1] };
      if (data.length > 2) { body.count = data[2]; }
    }
  }
  let member = util.toSnowflake(name);
  if (member) { member = aliases.findByKey(member); }
  if (member) { name = member.name; }
  name = cutil.urlSafeB64encode(name);
  httptool.doPost('/players/' + name + '/' + cmd, body);
}

export function banlist($) {
  const [httptool, message, data] = [$.httptool, $.message, [...$.data]];
  if (data.length < 2) return util.reactUnknown(message);
  const cmd = data.shift() + '-id';
  const body = { steamid: data.shift() };
  httptool.doPost('/banlist/' + cmd, body);
}

function whitelistRemoveName(httptool, name, dataHandler = null) {
  httptool.doPost('/whitelist/remove', { player: name }, dataHandler);
}

function whitelistAddName(httptool, name, pwd, dataHandler = null) {
  httptool.doPost('/whitelist/add', { player: name, password: pwd }, dataHandler);
}

function whitelistRemoveId(httptool, aliases, message, snowflake, dataHandler = null) {
  const record = aliases.findByKey(snowflake);
  if (!record) return util.reactError(message);
  whitelistRemoveName(httptool, record.name, dataHandler);
}

function whitelistAddId(context, httptool, aliases, message, snowflake, name = null) {
  let record = aliases.findByKey(snowflake);
  if (name) {
    snowflake = record ? record.snowflake : util.toSnowflake(snowflake);
    if (!snowflake) return util.reactError(message);
    if (record && record.name != name) {
      if (aliases.findByName(name)) return util.reactError(message);  // Someone else has name
      record = null;  // Force add alias again with changed name
    }
  } else {
    if (!record) return util.reactError(message);  // Need alias if no name given
    [snowflake, name] = [record.snowflake, record.name];
  }
  context.client.users.fetch(snowflake)
    .then(function(user) {
      if (!record) {
        const discordid = user.tag.replaceAll('#', '');
        if (!aliases.add(snowflake, discordid, name)) return util.reactError(message);
        aliases.save();
      }
      const pwd = Math.random().toString(16).substr(2, 8);
      whitelistAddName(httptool, name, pwd, function() {
        user.send(context.config.WHITELIST_DM.replace('${user}', name).replace('${pass}', pwd))
          .then(function() { util.reactSuccess(message); })
          .catch(function(error) { logger.error(error, message); });
      });
    })
    .catch(function(error) { logger.error(error, message); });
}

export function whitelist($) {
  const [context, httptool, aliases, message, data] = [$.context, $.httptool, $.aliases, $.message, [...$.data]];
  if (data.length < 2) return util.reactUnknown(message);
  const cmd = data.shift();
  if (cmd === 'add-name') {
    if (data.length < 2) return util.reactUnknown(message);
    whitelistAddName(httptool, data[0], data[1]);
  } else if (cmd === 'remove-name') {
    whitelistRemoveName(httptool, data[0]);
  } else if (cmd === 'add-id') {
    whitelistAddId(context, httptool, aliases, message, data[0], data.length > 1 ? data[1] : null);
  } else if (cmd === 'remove-id') {
    whitelistRemoveId(httptool, aliases, message, data[0]);
  } else if (cmd === 'reset-password') {
    whitelistRemoveId(httptool, aliases, message, data[0], function() {
      cutil.sleep(500).then(function() { whitelistAddId(context, httptool, aliases, message, data[0]); });
    });
  } else {
    util.reactUnknown(message);
  }
}
