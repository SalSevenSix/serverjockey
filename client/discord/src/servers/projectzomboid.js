'use strict';

const logger = require('../logger.js');
const util = require('../util.js');
const commons = require('../commons.js');
const helpText = {
  title: 'PROJECT ZOMBOID COMMANDS',
  help1: [
    'server                    : Server status',
    'server start              : Start server',
    'server restart            : Save world and restart server',
    'server stop               : Save world and stop server',
    'auto {mode}               : Set auto mode, valid values 0,1,2,3',
    'log                       : Get last 100 lines from the log',
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
    'whitelist add-name "{name}" "{pwd}" : Add player by name',
    'whitelist remove-name "{name}"      : Remove player by name',
    'whitelist add-id {discordid}        : Add player by discord id',
    'whitelist remove-id {discordid}     : Remove player by discord id',
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
  help: [
    'Show help text. Use {command} and {action} for more detailed information. Both optional.'
  ],
  playersetaccesslevel: [
    'Set access level for online player. Level options:',
    '`admin, moderator, overseer, gm, observer, none`'
  ],
  playergivexp: [
    'Give XP to online player. Skill options:',
    '```Fitness, Strength,',
    'Combat, Axe, Blunt, SmallBlunt, LongBlade, SmallBlade,',
    'Spear, Maintenance, Firearm, Aiming, Reloading,',
    'Agility, Sprinting, Lightfoot, Nimble, Sneak,',
    'Crafting, Woodwork, Cooking, Farming, Doctor,',
    'Electricity, MetalWelding, Mechanics, Tailoring,',
    'Survivalist, Fishing, Trapping, PlantScavenging```'
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
};


exports.startup = commons.startAllEventLogging;
exports.help = function($) { commons.sendHelp($, helpText); }
exports.server = commons.server;
exports.auto = commons.auto;
exports.log = commons.log;
exports.getconfig = commons.getconfig;
exports.setconfig = commons.setconfig;
exports.deployment = commons.deployment;
exports.players = commons.players;

exports.world = function($) {
  const data = [...$.data];
  if (data.length === 0) {
    $.message.react('❓');
    return;
  }
  const cmd = data.shift();
  let body = null;
  if (data.length > 0 && cmd === 'broadcast') {
    body = { message: data.join(' ') };
  }
  $.httptool.doPost('/world/' + cmd, body);
}

exports.player = function($) {
  const data = [...$.data];
  if (data.length < 2) {
    $.message.react('❓');
    return;
  }
  const name = util.urlSafeB64encode(data.shift());
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
      body = { module: data[0], item: data[1] };
    } else if (cmd === 'give-xp') {
      body = { skill: data[0], xp: data[1] };
    } else if (cmd === 'give-item') {
      body = { module: data[0], item: data[1] };
      if (data.length > 2) { body.count = data[2]; }
    }
  }
  $.httptool.doPost('/players/' + name + '/' + cmd, body);
}

exports.whitelist = function($) {
  const data = [...$.data];
  if (data.length < 2) {
    $.message.react('❓');
    return;
  }
  const cmd = data.shift();
  if (data[0].length > 3 && data[0].startsWith('<@') && data[0].endsWith('>')) {
    data[0] = data[0].slice(2, -1);
  }
  if (cmd === 'add-name') {
    if (data.length < 2) {
      $.message.react('❓');
      return;
    }
    $.httptool.doPost('/whitelist/add', { player: data[0], password: data[1] });
  } else if (cmd === 'remove-name') {
    $.httptool.doPost('/whitelist/remove', { player: data[0] });
  } else if (cmd === 'add-id') {
    $.context.client.users.fetch(data[0], true, true)
      .then(function(user) {
        const name = user.tag.replaceAll('#', '');
        const pwd = Math.random().toString(16).substr(2, 8);
        logger.info('Whitelist add-id: ' + data[0] + ' ' + name);
        $.httptool.doPost('/whitelist/add', { player: name, password: pwd }, function() {
          user.send($.context.config.WHITELIST_DM.replace('${user}', name).replace('${pass}', pwd))
            .then(function() { $.message.react('✅'); })
            .catch(function(error) { $.httptool.error(error, $.message); });
        });
      })
      .catch(function(error) {
        $.httptool.error(error, $.message);
      });
  } else if (cmd === 'remove-id') {
    $.context.client.users.fetch(data[0], true, true)
      .then(function(user) {
        const name = user.tag.replaceAll('#', '');
        logger.info('Whitelist remove-id: ' + data[0] + ' ' + name);
        $.httptool.doPost('/whitelist/remove', { player: name });
      })
      .catch(function(error) {
        $.httptool.error(error, $.message);
      });
  } else {
    $.message.react('❓');
  }
}

exports.banlist = function($) {
  const data = [...$.data];
  if (data.length < 2) {
    $.message.react('❓');
    return;
  }
  const cmd = data.shift() + '-id';
  const body = { steamid: data.shift() };
  $.httptool.doPost('/banlist/' + cmd, body);
}
