import * as cutil from 'common/util/util';
import * as util from '../util/util.js';
import * as logger from '../util/logger.js';
import * as msgutil from '../util/msgutil.js';
import * as helptext from '../helptext.js';
import * as commons from '../commons.js';

export const startup = commons.startupAll;
export const { status, server, auto, log, getconfig, setconfig, deployment, players, chat,
  alias, reward, trigger, activity, chatlog } = commons;

export const help = helptext.newServerHelpBuilder()
  .title('PROJECT ZOMBOID COMMANDS')
  .addServer(true, true).addChat()
  .addAlias().addReward().addTrigger().addActivity().addChatlog()
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
  .addHelp('player tele-to', [
    'Teleport the player named {name} to location of player named {toplayer}',
    'e.g. `!player "Mr Tee" tele-to "Jojo"`'])
  .addHelp('player tele-at', [
    'Teleport a player to the X,Y,Z location on the map.',
    'e.g. `!player "Mr Tee" tele-at 10339,9267,0`'])
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

export function world({ httptool, message, data }) {
  if (data.length === 0) return msgutil.reactUnknown(message);
  const cmd = data[0];
  let body = null;
  if (cmd === 'broadcast') {
    if (data.length < 2) return msgutil.reactUnknown(message);
    body = { message: data.slice(1).join(' ') };
  }
  httptool.doPost('/world/' + cmd, body);
}

export function player({ httptool, aliases, message, data }) {
  if (data.length < 2) return msgutil.reactUnknown(message);
  const cmd = data[1];
  let body = null;
  if (data.length > 2) {
    if (cmd === 'set-access-level') {
      body = { level: data[2] };
    } else if (cmd === 'tele-to') {
      body = { toplayer: data[2] };
    } else if (cmd === 'tele-at') {
      body = { location: data[2] };
    } else if (cmd === 'spawn-horde') {
      body = { count: data[2] };
    } else if (cmd === 'spawn-vehicle') {
      if (data.length < 4) return msgutil.reactUnknown(message);
      body = { module: data[2], item: data[3] };
    } else if (cmd === 'give-xp') {
      if (data.length < 4) return msgutil.reactUnknown(message);
      body = { skill: data[2], xp: data[3] };
    } else if (cmd === 'give-item') {
      if (data.length < 4) return msgutil.reactUnknown(message);
      body = { module: data[2], item: data[3] };
      if (data.length > 4) { body.count = data[4]; }
    }
  }
  let name = aliases.resolveName(data[0]);
  name = cutil.urlSafeB64encode(name);
  httptool.doPost('/players/' + name + '/' + cmd, body);
}

export function banlist({ httptool, message, data }) {
  if (data.length < 2) return msgutil.reactUnknown(message);
  httptool.doPost('/banlist/' + data[0] + '-id', { steamid: data[1] });
}

function whitelistRemoveName(httptool, name, dataHandler = null) {
  httptool.doPost('/whitelist/remove', { player: name }, dataHandler);
}

function whitelistAddName(httptool, name, pwd, dataHandler = null) {
  httptool.doPost('/whitelist/add', { player: name, password: pwd }, dataHandler);
}

function whitelistRemoveId(httptool, aliases, message, snowflake, dataHandler = null) {
  const record = aliases.findByKey(snowflake);
  if (!record) return msgutil.reactError(message);
  whitelistRemoveName(httptool, record.name, dataHandler);
}

function whitelistAddId(context, httptool, instance, aliases, message, snowflake, name = null) {
  let record = aliases.findByKey(snowflake);
  if (name) {
    snowflake = record ? record.snowflake : util.toSnowflake(snowflake);
    if (!snowflake) return msgutil.reactError(message);
    if (record && record.name != name) {
      if (aliases.findByName(name)) return msgutil.reactError(message);  // Someone else has name
      record = null;  // Force add alias again with changed name
    }
  } else {
    if (!record) return msgutil.reactError(message);  // Need alias if no name given
    [snowflake, name] = [record.snowflake, record.name];
  }
  context.client.users.fetch(snowflake)
    .then(function(user) {
      if (!record) {
        const discordid = user.tag.replaceAll('#', '');
        if (!aliases.add(snowflake, discordid, name)) return msgutil.reactError(message);
        aliases.save();
      }
      const pwd = Math.random().toString(16).substr(2, 8);
      whitelistAddName(httptool, name, pwd, function() {
        let text = context.config.WHITELIST_DM;
        text = text.replaceAll('${user}', name).replaceAll('${pass}', pwd);  // Legacy substitutes
        text = text.replaceAll('{instance}', instance).replaceAll('{user}', name).replaceAll('{pass}', pwd);
        user.send(text)
          .then(function() { msgutil.reactSuccess(message); })
          .catch(function(error) { logger.error(error, message); });
      });
    })
    .catch(function(error) { logger.error(error, message); });
}

export function whitelist({ context, httptool, instance, aliases, message, data }) {
  if (data.length < 2) return msgutil.reactUnknown(message);
  const cmd = data[0];
  if (cmd === 'add-name') {
    if (data.length < 3) return msgutil.reactUnknown(message);
    whitelistAddName(httptool, data[1], data[2]);
  } else if (cmd === 'remove-name') {
    whitelistRemoveName(httptool, data[1]);
  } else if (cmd === 'add-id') {
    whitelistAddId(context, httptool, instance, aliases, message, data[1], data.length > 2 ? data[2] : null);
  } else if (cmd === 'remove-id') {
    whitelistRemoveId(httptool, aliases, message, data[1]);
  } else if (cmd === 'reset-password') {
    whitelistRemoveId(httptool, aliases, message, data[1], function() {
      cutil.sleep(500).then(function() { whitelistAddId(context, httptool, instance, aliases, message, data[1]); });
    });
  } else {
    msgutil.reactUnknown(message);
  }
}
