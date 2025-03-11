import * as cutil from 'common/util/util';
import * as subs from '../util/subs.js';

/* eslint-disable complexity */
/* eslint-disable max-lines-per-function */
function newTriggerHandler(context, channel, instance, triggers) {
  const prelog = '`' + instance + '` 🔔 ';
  const cache = { channel: {}, role: {}, member: {} };
  const get = async function(fetcher, entity, snowflake) {
    if (cutil.hasProp(cache[entity], snowflake)) return cache[entity][snowflake];
    const fallback = entity === 'channel' ? channel : null;
    const result = await fetcher.fetch(snowflake);
    cache[entity][snowflake] = result ? result : fallback;
    return cache[entity][snowflake];
  };
  const getChannel = async function(snowflake) { return await get(context.client.channels, 'channel', snowflake); };
  const getRole = async function(snowflake) { return await get(channel.guild.roles, 'role', snowflake); };
  const getMember = async function(snowflake) { return await get(channel.guild.members, 'member', snowflake); };
  const handle = async function(trigger, event, alias) {
    if (event === 'LOGIN' && !cutil.hasProp(trigger, 'on-login')) return;
    if (event === 'LOGOUT' && !cutil.hasProp(trigger, 'on-logout')) return;
    if (event === 'DEATH' && !cutil.hasProp(trigger, 'on-death')) return;
    const member = await getMember(alias.snowflake);
    if (!member) return;
    for (const [isReq, rqRole] of [[true, 'rq-role'], [false, 'rq-not-role']]) {
      if (cutil.hasProp(trigger, rqRole)) {
        const role = await getRole(trigger[rqRole].snowflake);
        if (!role) return;
        const found = member.roles.cache.find(function(memberRole) { return memberRole.id === role.id; });
        if (isReq && !found) return;
        if (!isReq && found) return;
      }
    }
    let actionChannel = channel;
    if (cutil.hasProp(trigger, 'cx-channel')) { actionChannel = await getChannel(trigger['cx-channel'].snowflake); }
    if (cutil.hasProp(trigger, 'cx-delay')) { await cutil.sleep(trigger['cx-delay'] * 1000 - 1000); }
    for (const [isAdd, doRole] of [[true, 'do-add-role'], [false, 'do-remove-role']]) {
      if (cutil.hasProp(trigger, doRole)) {
        const role = await getRole(trigger[doRole].snowflake);
        if (!role) return;
        await cutil.sleep(1000);
        if (isAdd) { await member.roles.add(role); }
        else { await member.roles.remove(role); }
        actionChannel.send(prelog + '`@' + alias.discordid + (isAdd ? '` 👍 `@' : '` 👎 `@') + role.name + '`');
      }
    }
    if (cutil.hasProp(trigger, 'do-message')) {
      await cutil.sleep(1000);
      let text = trigger['do-message'];
      text = text.replaceAll('{n}', '\n');
      text = text.replaceAll('{!}', context.config.CMD_PREFIX);
      text = text.replaceAll('{instance}', instance);
      text = text.replaceAll('{channel}', actionChannel.name);
      text = text.replaceAll('{event}', event.toLowerCase());
      text = text.replaceAll('{member}', alias.discordid);
      text = text.replaceAll('{playername}', alias.name);
      text = text.replaceAll('{player}', '"' + alias.name + '"');
      actionChannel.send(text);
    }
  };
  return async function(event, alias) {
    if (event === 'CLEAR') { [cache.channel, cache.role, cache.member] = [{}, {}, {}]; }
    if (!alias) return;
    for (const trigger of triggers.list()) { await handle(trigger, event, alias); }
  };
}
/* eslint-enable max-lines-per-function */
/* eslint-enable complexity */

function startPlayerEvents($) {
  const [context, channels, aliases, instance, url] = [$.context, $.channels, $.aliases, $.instance, $.url];
  if (!channels.login && !channels.chat) return;
  const triggerHandler = channels.login ? newTriggerHandler(context, channels.login, instance, $.triggers) : null;
  new subs.Helper(context).daemon(url + '/players/subscribe', function(json) {
    if (json.event === 'CLEAR') {
      if (triggerHandler) { triggerHandler(json.event, null); }
      return true;
    }
    let playerName = json.player && json.player.name ? json.player.name : null;
    if (!playerName) return true;
    const playerAlias = aliases.findByName(playerName);
    if (playerAlias) { playerName += ' `@' + playerAlias.discordid + '`'; }
    if (json.event === 'CHAT') {
      if (!channels.chat) return true;
      channels.chat.send('`' + instance + '` 💬 ' + playerName + ': ' + json.text);
      return true;
    }
    if (!channels.login) return true;
    let result = null;
    if (json.event === 'LOGIN') { result = ' 🟢 '; }
    else if (json.event === 'LOGOUT') { result = ' 🔴 '; }
    else if (json.event === 'DEATH') { result = ' 💀 '; }
    if (!result) return true;
    result = '`' + instance + '`' + result + playerName;
    if (json.text) { result += ' [' + json.text + ']'; }
    if (json.player.steamid) { result += ' [' + json.player.steamid + ']'; }
    channels.login.send(result);
    if (triggerHandler && playerAlias) { triggerHandler(json.event, playerAlias); }
    return true;
  });
}

function startServerEvents($) {
  const [context, channels, instance, url] = [$.context, $.channels, $.instance, $.url];
  if (!channels.server) return;
  let [state, restartRequired] = ['READY', false];
  new subs.Helper(context).daemon(url + '/server/subscribe', function(json) {
    if (!json.state) return true;  // Ignore no state
    if (json.state === 'START') return true;  // Ignore transient state
    if (!restartRequired && json.details.restart) {
      channels.server.send('`' + instance + '` 🔄 restart required');
      restartRequired = true;
      return true;
    }
    if (state === json.state) return true;  // Ignore no state change
    state = json.state;
    if (state === 'STARTED') { restartRequired = false; }
    channels.server.send('`' + instance + '` 📡 ' + state);
    return true;
  });
}

export function startupServerOnly($) {
  startServerEvents($);
}

export function startupAll($) {
  startServerEvents($);
  startPlayerEvents($);
}
