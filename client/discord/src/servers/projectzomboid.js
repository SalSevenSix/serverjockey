const cutil = require('common/util/util');
const util = require('../util.js');
const logger = require('../logger.js');
const helptext = require('../helptext.js');
const commons = require('../commons.js');

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
    'player "{name}" lightning           : Trigger lightning',
    'player "{name}" thunder             : Trigger thunder',
    'whitelist add-id {discordid}        : Add player by discord id',
    'whitelist remove-id {discordid}     : Remove player by discord id',
    'whitelist add-for {discordid} "{name}" : Add player for discord id',
    'whitelist add-name "{name}" "{pwd}" : Add player by name',
    'whitelist remove-name "{name}"      : Remove player by name',
    'whitelist reset-password {discordid} "{name}" : experimental',
    'banlist add {steamid}     : Add player SteamID to banlist',
    'banlist remove {steamid}  : Remove player SteamID from banlist'
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
    'deployment wipe-world-playerdb    : Delete only player DB',
    'deployment wipe-world-config      : Delete only config files',
    'deployment wipe-world-all         : Delete game world folder',
    'deployment install-runtime {beta} : Install game server'
  ],
  alias: helptext.alias,
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

export const [startup, help, server, auto, log,
  getconfig, setconfig, deployment, players, activity, alias] = [
  commons.startAllEventLogging, helptext.help(helpData), commons.server, commons.auto, commons.log,
  commons.getconfig, commons.setconfig, commons.deployment, commons.players, commons.activity, commons.alias];

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
  const [httptool, message, data] = [$.httptool, $.message, [...$.data]];
  if (data.length < 2) return util.reactUnknown(message);
  const name = cutil.urlSafeB64encode(data.shift());
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

function whitelistRemoveId(context, httptool, aliases, message, snowflake, dataHandler = null) {
  snowflake = util.toSnowflake(snowflake);
  if (!snowflake) return util.reactError(message);
  context.client.users.fetch(snowflake, true, true)
    .then(function(user) {
      whitelistRemoveName(httptool, user.tag.replaceAll('#', ''), dataHandler);
      if (aliases && aliases.remove(snowflake)) { aliases.save(); }
    })
    .catch(function(error) {
      logger.error(error, message);
    });
}

function whitelistAddId(context, httptool, aliases, message, snowflake, name = null) {
  snowflake = util.toSnowflake(snowflake);
  if (!snowflake) return util.reactError(message);
  context.client.users.fetch(snowflake, true, true)
    .then(function(user) {
      const [discordid, pwd] = [user.tag.replaceAll('#', ''), Math.random().toString(16).substr(2, 8)];
      if (!name) { name = discordid; }
      whitelistAddName(httptool, name, pwd, function() {
        user.send(context.config.WHITELIST_DM.replace('${user}', name).replace('${pass}', pwd))
          .then(function() {
            if (aliases && aliases.add(snowflake, discordid, name)) { aliases.save(); }
            util.reactSuccess(message);
          })
          .catch(function(error) { logger.error(error, message); });
      });
    })
    .catch(function(error) {
      logger.error(error, message);
    });
}

export function whitelist($) {
  const [context, httptool, aliases, message, data] = [$.context, $.httptool, $.aliases, $.message, [...$.data]];
  if (data.length < 2) return util.reactUnknown(message);
  const cmd = data.shift();
  if (cmd === 'add-id') {
    whitelistAddId(context, httptool, aliases, message, data[0]);
  } else if (cmd === 'add-for') {
    if (data.length < 2) return util.reactUnknown(message);
    whitelistAddId(context, httptool, aliases, message, data[0], data[1]);
  } else if (cmd === 'add-name') {
    if (data.length < 2) return util.reactUnknown(message);
    whitelistAddName(httptool, data[0], data[1]);
  } else if (cmd === 'remove-id') {
    whitelistRemoveId(context, httptool, aliases, message, data[0]);
  } else if (cmd === 'remove-name') {
    whitelistRemoveName(httptool, data[0]);
  } else if (cmd === 'reset-password') {
    if (data.length < 2) {
      whitelistRemoveId(context, httptool, null, message, data[0], function() {
        cutil.sleep(500).then(function() { whitelistAddId(context, httptool, null, message, data[0]); });
      });
    } else {
      whitelistRemoveName(httptool, data[1], function() {
        cutil.sleep(500).then(function() { whitelistAddId(context, httptool, null, message, data[0], data[1]); });
      });
    }
  } else {
    util.reactUnknown(message);
  }
}
