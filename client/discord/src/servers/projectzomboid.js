import * as cutil from 'common/util/util';
import * as util from '../util/util.js';
import * as logger from '../util/logger.js';
import * as helptext from '../helptext.js';
import * as commons from '../commons.js';

export const startup = commons.startupAll;
export const { server, auto, log, getconfig, setconfig, deployment, players,
  alias, reward, trigger, activity } = commons;

export const help = helptext.newServerHelpBuilder()
  .title('PROJECT ZOMBOID COMMANDS')
  .addServer(true, true)
  .addAlias().addReward().addTrigger().addActivity()
  .add([
    'world save                : Save the game world',
    'world broadcast {message} : Broadcast message to all players',
    'world chopper             : Trigger chopper event',
    'world gunshot             : Trigger gunshot event',
    'world start-storm         : Start a storm',
    'world stop-weather        : Stop current weather',
    'world start-rain          : Start rain',
    'world stop-rain           : Stop rain'])
  .next()
  .addPlayers()
  .add([
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
    'banlist remove {steamid}       : Remove player SteamID from banlist'])
  .next()
  .addConfig(['cmdargs', 'INI', 'Sandbox', 'Spawnregions', 'Spawnpoints', 'JVM'])
  .addDeployment()
  .addHelp('player set-access-level', [
    'Set access level for online player. Level options:', '```',
    'admin, moderator, overseer, gm, observer, none', '```'])
  .addHelp('player give-xp', [
    'Give XP to online player. Skill options:', '```',
    'Sprinting, Lightfoot, Nimble, Sneak, Aiming, Reloading,',
    'Axe, SmallBlunt, Blunt, Spear, SmallBlade, LongBlade, Combat,',
    'Woodwork, Cooking, Farming, Doctor, Electricity, MetalWelding,',
    'Tailoring, Mechanics, FlintKnapping, Carving, Masonry, Pottery,',
    'Fishing, Trapping, PlantScavenging, Fitness, Strength', '```'])
  .addHelp('player give-item', [
    'Give item to player, {count} is optional.'])
  .addHelp('player spawn-vehicle', [
    'Spawn a vehicle next to player. Condition will vary.'])
  .build();

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

function whitelistAddId(context, httptool, instance, aliases, message, snowflake, name = null) {
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
        let text = context.config.WHITELIST_DM;
        text = text.replaceAll('${user}', name).replaceAll('${pass}', pwd);  // Legacy substitutes
        text = text.replaceAll('{instance}', instance).replaceAll('{user}', name).replaceAll('{pass}', pwd);
        user.send(text)
          .then(function() { util.reactSuccess(message); })
          .catch(function(error) { logger.error(error, message); });
      });
    })
    .catch(function(error) { logger.error(error, message); });
}

export function whitelist($) {
  const [context, httptool, instance, aliases, message, data] = [
    $.context, $.httptool, $.instance, $.aliases, $.message, [...$.data]];
  if (data.length < 2) return util.reactUnknown(message);
  const cmd = data.shift();
  if (cmd === 'add-name') {
    if (data.length < 2) return util.reactUnknown(message);
    whitelistAddName(httptool, data[0], data[1]);
  } else if (cmd === 'remove-name') {
    whitelistRemoveName(httptool, data[0]);
  } else if (cmd === 'add-id') {
    whitelistAddId(context, httptool, instance, aliases, message, data[0], data.length > 1 ? data[1] : null);
  } else if (cmd === 'remove-id') {
    whitelistRemoveId(httptool, aliases, message, data[0]);
  } else if (cmd === 'reset-password') {
    whitelistRemoveId(httptool, aliases, message, data[0], function() {
      cutil.sleep(500).then(function() { whitelistAddId(context, httptool, instance, aliases, message, data[0]); });
    });
  } else {
    util.reactUnknown(message);
  }
}
