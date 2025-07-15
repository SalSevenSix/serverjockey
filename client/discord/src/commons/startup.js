import * as cutil from 'common/util/util';
import * as util from '../util/util.js';
import * as logger from '../util/logger.js';
import * as subs from '../util/subs.js';

const serverEventMap = { STARTED: 'on-started', STOPPED: 'on-stopped', EXCEPTION: 'on-stopped' };
const playerEventMap = { LOGIN: 'on-login', LOGOUT: 'on-logout', DEATH: 'on-death' };

function newChatbotHandler(context, instance, url) {
  // TODO locking? requests should be serial
  const gamename = context.instancesService.getModuleName(instance);
  return function(playerName, input) {
    if (!input || !input.startsWith(context.config.CMD_PREFIX)) return;
    input = input.slice(context.config.CMD_PREFIX.length).trim();
    logger.info('AI| ' + playerName + ' (' + instance + ') : ' + input);
    context.llmClient.chatbot({ input, gamename }).then(function(text) {
      const request = util.newPostRequest('application/json', context.config.SERVER_TOKEN);
      request.body = JSON.stringify({ player: '@', text: text });
      fetch(url + '/console/say', request)
        .then(function(response) { if (!response.ok) throw new Error('Status: ' + response.status); })
        .catch(logger.error);
    });
  };
}

/* eslint-disable max-depth */
/* eslint-disable complexity */
/* eslint-disable max-lines-per-function */
function newTriggerHandler(context, channels, instance, triggers) {
  const prelog = '`' + instance + '` 🔔 ';
  const cache = {};

  const resetCache = function() {
    [cache.guild, cache.channel, cache.role, cache.member] = [null, {}, {}, {}];
    Object.values(channels).forEach(function(channel) {
      if (!channel) return;
      if (!cache.guild) { cache.guild = channel.guild; }
      cache.channel[channel.id] = channel;
    });
  };

  const get = async function(entity, fetcher, snowflake, fallback = null) {
    if (cutil.hasProp(cache[entity], snowflake)) return cache[entity][snowflake];
    const result = await fetcher.fetch(snowflake);
    cache[entity][snowflake] = result ? result : fallback;
    return cache[entity][snowflake];
  };

  const getRole = async function(snowflake) {
    return await get('role', cache.guild.roles, snowflake);
  };

  const subsText = function(value, channel, event, alias = null) {
    let result = value.replaceAll('{n}', '\n');
    result = result.replaceAll('{!}', context.config.CMD_PREFIX);
    result = result.replaceAll('{instance}', instance);
    result = result.replaceAll('{channel}', channel.name);
    result = result.replaceAll('{event}', event.toLowerCase());
    if (alias && alias.name) {
      result = result.replaceAll('{playername}', alias.name);
      result = result.replaceAll('{player}', '"' + alias.name + '"');
    }
    if (alias && alias.discordid) {
      result = result.replaceAll('{member}', alias.discordid);
    }
    return result;
  };

  const processTriggerContext = async function(trigger, channel) {
    let result = channel;
    if (cutil.hasProp(trigger, 'cx-channel')) {
      result = await get('channel', context.client.channels, trigger['cx-channel'].snowflake, channel);
    }
    if (cutil.hasProp(trigger, 'cx-delay')) {
      await cutil.sleep(trigger['cx-delay'] * 1000 - 1000);
    }
    return result;
  };

  const handleServerEvent = async function(trigger, event) {
    if (!trigger['on-event'].includes(serverEventMap[event])) return;  // Check applicable event
    if (!cutil.hasProp(trigger, 'do-message')) return;  // Nothing to do
    const channel = await processTriggerContext(trigger, channels.server);  // Process context values
    for (const triggerMessage of trigger['do-message']) {  // Process message actions
      await cutil.sleep(1000);
      channel.send(subsText(triggerMessage, channel, event));
    }
  };

  const handlePlayerEvent = async function(trigger, event, alias) {
    if (!trigger['on-event'].includes(playerEventMap[event])) return;  // Check applicable event
    const member = alias && alias.snowflake ? await get('member', cache.guild.members, alias.snowflake) : null;
    if (cutil.hasProp(trigger, 'rq-not-role')) {  // Member cannot have any of these roles
      if (!member) return;
      for (const triggerRole of trigger['rq-not-role']) {
        const role = await getRole(triggerRole.snowflake);
        if (!role) return;
        const found = member.roles.cache.find(function(memberRole) { return memberRole.id === role.id; });
        if (found) return;
      }
    }
    if (cutil.hasProp(trigger, 'rq-role')) {  // Member must have at least one of these roles
      if (!member) return;
      let found = false;
      for (const triggerRole of trigger['rq-role']) {
        if (!found) {
          const role = await getRole(triggerRole.snowflake);
          if (!role) return;
          found ||= member.roles.cache.find(function(memberRole) { return memberRole.id === role.id; });
        }
      }
      if (!found) return;
    }
    const channel = await processTriggerContext(trigger, channels.login);  // Process context values
    for (const [isAdd, doRole] of [[false, 'do-remove-role'], [true, 'do-add-role']]) {  // Process role actions
      if (member && alias && alias.discordid && cutil.hasProp(trigger, doRole)) {
        for (const triggerRole of trigger[doRole]) {
          const role = await getRole(triggerRole.snowflake);
          if (role) {
            const found = member.roles.cache.find(function(memberRole) { return memberRole.id === role.id; });
            if ((isAdd && !found) || (!isAdd && found)) {
              await cutil.sleep(1000);
              if (isAdd) { await member.roles.add(role); }
              else { await member.roles.remove(role); }
              channel.send(prelog + '`@' + alias.discordid + (isAdd ? '` 👍 `@' : '` 👎 `@') + role.name + '`');
            }
          }
        }
      }
    }
    if (cutil.hasProp(trigger, 'do-message')) {  // Process message actions
      for (const triggerMessage of trigger['do-message']) {
        await cutil.sleep(1000);
        channel.send(subsText(triggerMessage, channel, event, alias));
      }
    }
  };

  resetCache();
  return async function(event, alias = null) {
    if (cutil.hasProp(playerEventMap, event)) {
      for (const trigger of triggers.list()) { await handlePlayerEvent(trigger, event, alias); }
    } else if (cutil.hasProp(serverEventMap, event)) {
      for (const trigger of triggers.list()) { await handleServerEvent(trigger, event); }
    }
    if (event === 'CLEAR') { resetCache(); }
  };
}
/* eslint-enable max-lines-per-function */
/* eslint-enable complexity */
/* eslint-enable max-depth */


function startPlayerEvents(context, channels, instance, url, aliases, triggerHandler, chatbotHandler) {
  new subs.Helper(context).daemon(url + '/players/subscribe', function(json) {
    if (json.event === 'CLEAR') {
      if (triggerHandler) { triggerHandler(json.event); }
      return true;
    }
    let playerName = json.player && json.player.name ? json.player.name : null;
    if (!playerName) return true;
    const playerAlias = aliases.findByName(playerName);
    if (playerAlias) { playerName += ' `@' + playerAlias.discordid + '`'; }
    if (json.event === 'CHAT') {
      if (chatbotHandler) { chatbotHandler(playerName, json.text); }
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
    if (triggerHandler) { triggerHandler(json.event, playerAlias ? playerAlias : { name: playerName }); }
    return true;
  });
}

function startServerEvents(context, channels, instance, url, triggerHandler) {
  let [state, restartRequired] = [null, false];
  new subs.Helper(context).daemon(url + '/server/subscribe', function(json) {
    if (!json.state) return true;  // Ignore no state
    if (!state) { state = json.state; }  // Set initial state
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
    if (triggerHandler) { triggerHandler(state); }
    return true;
  });
}

export function startupServerOnly({ context, channels, instance, url, triggers }) {
  if (!channels.server) return;
  const triggerHandler = newTriggerHandler(context, channels, instance, triggers);
  startServerEvents(context, channels, instance, url, triggerHandler);
}

export function startupAll({ context, channels, instance, url, triggers, aliases }) {
  const triggerHandler = channels.server || channels.login
    ? newTriggerHandler(context, channels, instance, triggers) : null;
  const chatbotHandler = newChatbotHandler(context, instance, url);  // TODO consider when not supported for instance
  if (channels.server) {
    startServerEvents(context, channels, instance, url, triggerHandler);
  }
  if (channels.login || channels.chat) {
    startPlayerEvents(context, channels, instance, url, aliases, triggerHandler, chatbotHandler);
  }
}
