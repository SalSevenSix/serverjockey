import * as cutil from 'common/util/util';
import { emojis } from '../util/literals.js';
import * as util from '../util/util.js';
import * as logger from '../util/logger.js';
import * as subs from '../util/subs.js';

const serverEventMap = { STARTED: 'on-started', STOPPED: 'on-stopped', EXCEPTION: 'on-stopped' };
const playerEventMap = { LOGIN: 'on-login', LOGOUT: 'on-logout', DEATH: 'on-death' };

function newAliasmeHandler(instance, channel, aliases) {
  return function(text, name) {
    if (!name || !text) return;
    const alias = aliases.aliasmeCheck(name, text);
    if (!alias) return;
    aliases.save();
    cutil.sleep(500).then(function() {
      channel.send('`' + instance + '` ' + emojis.link + ' ' + alias.name + ' is alias of <@' + alias.snowflake + '>');
    });
  };
}

function newChatbotHandler(context, instance, url) {
  const data = { chatbot: null };

  fetch(url + '/console/say', util.newPostRequest('application/json', context.config.SERVER_TOKEN))
    .then(function(response) {
      if ([200, 204, 400, 409].includes(response.status)) {  // This confirms the Say service is available
        data.chatbot = context.llmClient.newChatbot(context.instancesService.getModuleName(instance));
      }
    })
    .catch(logger.error);

  return function(input) {
    if (!data.chatbot || !input || !input.startsWith(context.config.CMD_PREFIX)) return;
    if (input.trim() === context.config.CMD_PREFIX) return data.chatbot.reset();
    data.chatbot.request(input.slice(context.config.CMD_PREFIX.length).trim())
      .then(function(text) {
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
  const prelog = '`' + instance + '` ' + emojis.bell + ' ';
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
    if (!alias) return result;
    const player = alias.name;
    if (player) { result = result.replaceAll('{playername}', player).replaceAll('{player}', '"' + player + '"'); }
    const member = alias.discordid ? alias.discordid : player;
    if (member) { result = result.replaceAll('{member}', member); }
    const atmember = alias.snowflake ? '<@' + alias.snowflake + '>' : member;
    if (atmember) { result = result.replaceAll('{atmember}', atmember); }
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
    if (cutil.hasProp(trigger, 'rq-member')) {  // Must meet member condition
      if (trigger['rq-member'] && !member) return;
      if (!trigger['rq-member'] && member) return;
    }
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
              const thumbs = isAdd ? emojis.thumbsup : emojis.thumbsdown;
              channel.send(prelog + '`@' + alias.discordid + '` ' + thumbs + ' `@' + role.name + '`');
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
    if (member && cutil.hasProp(trigger, 'do-dm')) {  // Process DM action
      const text = [];
      for (const triggerMessage of trigger['do-dm']) {
        text.push(subsText(triggerMessage, channel, event, alias));
      }
      await cutil.sleep(1000);
      member.send(text.join('\n\n'));
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


function startPlayerEvents(context, channels, instance, url, aliases, triggerHandler, aliasmeHandler, chatbotHandler) {
  new subs.Helper(context).daemon(url + '/players/subscribe', function(json) {
    const [event, text] = [json.event, json.text];
    if (event === 'CLEAR') {
      if (triggerHandler) { triggerHandler(event); }
      return true;
    }
    const name = json.player && json.player.name ? json.player.name : null;
    if (!name) return true;
    const alias = aliases.findByName(name);
    const displayName = alias ? name + ' `@' + alias.discordid + '`' : name;
    if (event === 'CHAT') {
      if (aliasmeHandler) { aliasmeHandler(text, name); }
      if (chatbotHandler) { chatbotHandler(text); }
      if (!channels.chat) return true;
      channels.chat.send('`' + instance + '` ' + emojis.say + ' ' + displayName + ': ' + text);
      return true;
    }
    if (!channels.login) return true;
    let result = null;
    if (event === 'LOGIN') { result = emojis.greendot; }
    else if (event === 'LOGOUT') { result = emojis.reddot; }
    else if (event === 'DEATH') { result = emojis.skull; }
    if (!result) return true;
    result = '`' + instance + '` ' + result + ' ' + displayName;
    if (text) { result += ' [' + text + ']'; }
    if (json.player.steamid) { result += ' [' + json.player.steamid + ']'; }
    channels.login.send(result);
    if (triggerHandler) { triggerHandler(event, alias ? alias : { name: name }); }
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
      channels.server.send('`' + instance + '` ' + emojis.restart + ' restart required');
      restartRequired = true;
      return true;
    }
    if (state === json.state) return true;  // Ignore no state change
    state = json.state;
    if (state === 'STARTED') { restartRequired = false; }
    let text = '`' + instance + '` ' + emojis.satellite + ' ' + state;
    if (['READY', 'STARTED', 'STOPPED'].includes(state) && json.sincelaststate) {
      let seconds = json.sincelaststate / 1000;
      seconds = seconds.toFixed(seconds < 10.0 ? 1 : 0);
      text += ' in ' + seconds + ' seconds';
    } else if (state === 'EXCEPTION' && json.details && json.details.error) {
      text += ' [' + json.details.error + ']';
    }
    channels.server.send(text);
    if (triggerHandler) { triggerHandler(state); }
    return true;
  });
}

export function startupServerOnly({ context, channels, instance, url, triggers }) {
  channels = channels.resolve();
  if (!channels.server) return;
  const triggerHandler = newTriggerHandler(context, channels, instance, triggers);
  startServerEvents(context, channels, instance, url, triggerHandler);
}

export function startupAll({ context, channels, instance, url, triggers, aliases }) {
  channels = channels.resolve();
  const triggerHandler = channels.server || channels.login
    ? newTriggerHandler(context, channels, instance, triggers) : null;
  if (channels.server) {
    startServerEvents(context, channels, instance, url, triggerHandler);
  }
  if (channels.login || channels.chat) {
    const aliasmeHandler = newAliasmeHandler(instance, channels.chat ? channels.chat : channels.login, aliases);
    const chatbotHandler = newChatbotHandler(context, instance, url);
    startPlayerEvents(context, channels, instance, url, aliases, triggerHandler, aliasmeHandler, chatbotHandler);
  }
}
