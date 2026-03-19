import * as cutil from 'common/util/util';
import { playerEvents, serverEventTriggers, playerEventTriggers, emojis } from '../util/literals.js';
import * as logger from '../util/logger.js';

function newEntityLoader(context) {
  const [self, cache] = [{}, {}];

  const get = async function(entity, fetcher, snowflake) {
    if (cutil.hasProp(cache[entity], snowflake)) return cache[entity][snowflake];
    const result = await fetcher.fetch(snowflake).catch(logger.error);
    cache[entity][snowflake] = result ? result : null;
    return cache[entity][snowflake];
  };

  self.hasGuild = function() {
    if (!cache.guild) { cache.guild = context.channels.findGuild(); }
    if (cache.guild) return true;
    return false;
  };

  self.reset = function() {
    self.hasGuild();  // Just to find it
    [cache.channel, cache.role, cache.member] = [{}, {}, {}];
    return self;
  };

  self.getChannel = async function(snowflake) {
    return await get('channel', context.channels, snowflake);
  };

  self.getRole = async function(snowflake) {
    if (!cache.guild) return null;
    return await get('role', cache.guild.roles, snowflake);
  };

  self.getMember = async function(snowflake) {
    if (!cache.guild) return null;
    return await get('member', cache.guild.members, snowflake);
  };

  return self.reset();
}

async function roleModify(prelog, channel, discordid, member, role, isAdd) {
  const [discordName, roleName] = [' `@' + discordid + '` ', ' `@' + role.name + '` '];
  const [action, thumbs, promise] = isAdd
    ? ['add', emojis.thumbsup, member.roles.add(role)]
    : ['remove', emojis.thumbsdown, member.roles.remove(role)];
  const text = await promise.catch(logger.error)
    ? emojis.bell + discordName + thumbs + roleName
    : emojis.bang + ' Failed to ' + action + roleName + 'for member' + discordName + '(please check role order)';
  if (channel) { channel.send(prelog + text.trim()); }
}

/* eslint-disable max-depth */
/* eslint-disable complexity */
/* eslint-disable max-lines-per-function */
export function newTriggerHandler(context, channels, instance, triggers) {
  const [loader, prelog] = [newEntityLoader(context), '`' + instance + '` '];

  const subsText = function(value, channel, event, alias = null) {
    let result = value.replaceAll('{n}', '\n');
    result = result.replaceAll('{!}', context.config.CMD_PREFIX);
    result = result.replaceAll('{instance}', instance);
    result = result.replaceAll('{event}', event.toLowerCase());
    if (channel) { result = result.replaceAll('{channel}', channel.name); }
    if (!alias) return result;
    const player = alias.name;
    if (player) { result = result.replaceAll('{playername}', player).replaceAll('{player}', '"' + player + '"'); }
    const member = alias.discordid ? alias.discordid : player;
    if (member) { result = result.replaceAll('{member}', member); }
    const atmember = alias.snowflake ? '<@' + alias.snowflake + '>' : member;
    if (atmember) { result = result.replaceAll('{atmember}', atmember); }
    return result;
  };

  const processTriggerContext = async function(trigger, fallbackChannel) {
    let channel = fallbackChannel;
    if (cutil.hasProp(trigger, 'cx-channel')) {
      channel = await loader.getChannel(trigger['cx-channel'].snowflake);
      if (!channel) { channel = fallbackChannel; }
    }
    if (cutil.hasProp(trigger, 'cx-delay')) {
      await cutil.sleep(trigger['cx-delay'] * 1000 - 1000);
    }
    return channel;
  };

  const handleServerEvent = async function(trigger, event) {
    if (!trigger['on-event'].includes(serverEventTriggers[event])) return;  // Check applicable event
    if (!cutil.hasProp(trigger, 'do-message')) return;  // Nothing to do
    const channel = await processTriggerContext(trigger, channels.resolve().server);  // Process context values
    if (!channel) return;
    for (const triggerMessage of trigger['do-message']) {  // Process message actions
      await cutil.sleep(1000);
      channel.send(subsText(triggerMessage, channel, event));
    }
  };

  const handlePlayerEvent = async function(trigger, event, alias) {
    if (!trigger['on-event'].includes(playerEventTriggers[event])) return;  // Check applicable event
    if (!loader.hasGuild()) return;  // Cannot do anything without at least one channel
    const member = alias && alias.snowflake ? await loader.getMember(alias.snowflake) : null;
    if (cutil.hasProp(trigger, 'rq-member')) {  // Must meet member condition
      if (trigger['rq-member'] && !member) return;
      if (!trigger['rq-member'] && member) return;
    }
    if (cutil.hasProp(trigger, 'rq-not-role')) {  // Member cannot have any of these roles
      if (!member) return;
      for (const triggerRole of trigger['rq-not-role']) {
        const role = await loader.getRole(triggerRole.snowflake);
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
          const role = await loader.getRole(triggerRole.snowflake);
          if (!role) return;
          found ||= member.roles.cache.find(function(memberRole) { return memberRole.id === role.id; });
        }
      }
      if (!found) return;
    }
    const channel = await processTriggerContext(trigger, channels.resolve().login);  // Process context values
    for (const [isAdd, doRole] of [[false, 'do-remove-role'], [true, 'do-add-role']]) {  // Process role actions
      if (member && alias && alias.discordid && cutil.hasProp(trigger, doRole)) {
        for (const triggerRole of trigger[doRole]) {
          const role = await loader.getRole(triggerRole.snowflake);
          if (role) {
            const found = member.roles.cache.find(function(memberRole) { return memberRole.id === role.id; });
            if ((isAdd && !found) || (!isAdd && found)) {
              await cutil.sleep(1000);
              await roleModify(prelog, channel, alias.discordid, member, role, isAdd);
            }
          }
        }
      }
    }
    if (channel && cutil.hasProp(trigger, 'do-message')) {  // Process message actions
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

  return async function(event, alias = null) {
    if (cutil.hasProp(playerEventTriggers, event)) {
      for (const trigger of triggers.list()) { await handlePlayerEvent(trigger, event, alias); }
    } else if (cutil.hasProp(serverEventTriggers, event)) {
      for (const trigger of triggers.list()) { await handleServerEvent(trigger, event); }
    }
    if (event === playerEvents.clear) { loader.reset(); }
  };
}
/* eslint-enable max-lines-per-function */
/* eslint-enable complexity */
/* eslint-enable max-depth */
