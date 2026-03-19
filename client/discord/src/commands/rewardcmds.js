import * as cutil from 'common/util/util';
import * as pstats from 'common/activity/player';
import { emojis } from '../util/literals.js';
import * as util from '../util/util.js';
import * as logger from '../util/logger.js';
import * as http from '../util/http.js';
import * as msgutil from '../util/msgutil.js';

async function roleModify(prelog, channel, memberid, member, role, isAdd) {
  const [memberName, roleName] = [' `@' + memberid + '` ', ' `@' + role.name + '` '];
  const [action, thumbs, promise] = isAdd
    ? ['add', emojis.thumbsup, member.roles.add(role)]
    : ['remove', emojis.thumbsdown, member.roles.remove(role)];
  const text = await promise.catch(logger.error)
    ? emojis.medal + memberName + thumbs + roleName
    : emojis.bang + ' Failed to ' + action + roleName + 'for member' + memberName + '(please check role order)';
  channel.send(prelog + text.trim());
}

/* eslint-disable complexity */
/* eslint-disable max-lines-per-function */
async function evaluateRewards(context, aliases, rewards, instance, message) {
  const [now, prelog] = [Date.now(), '`' + instance + '` '];
  let schemes = rewards.list();
  if (schemes.length === 0) return;
  msgutil.reactWait(message);
  const [membersMap, roleMap, activityMap] = [{}, {}, {}];
  const allMembers = await message.guild.members.fetch();  // Fetch all members first to populate cache
  allMembers.forEach(function(member) { membersMap[member.id] = member; });
  for (const scheme of schemes) {  // Gather roles and thier members by snowflake
    if (!cutil.hasProp(roleMap, scheme.snowflake)) {
      await cutil.sleep(1000);
      const role = await message.guild.roles.fetch(scheme.snowflake).catch(logger.error);
      let schemeRole = null;
      if (role) {
        schemeRole = { role: role };
        schemeRole.orig = role.members.map(function(member) { return member.id; });
        schemeRole.members = [...schemeRole.orig];
      } else {
        message.channel.send(prelog + emojis.bang + ' Role `@' + scheme.roleid + '` not found');
      }
      roleMap[scheme.snowflake] = schemeRole;
    }
  }
  for (const snowflake of Object.keys(roleMap)) {  // Delete invalid roles
    if (!roleMap[snowflake]) { delete roleMap[snowflake]; }
  }
  schemes = schemes.filter(function(scheme) {  // Remove schemes with invalid role
    return cutil.hasProp(roleMap, scheme.snowflake);
  });
  if (schemes.length === 0) return;
  for (const scheme of schemes) {  // Gather activity by range
    if (!cutil.hasProp(activityMap, scheme.range)) {
      const atfrom = now - cutil.rangeCodeToMillis(scheme.range);
      const fetched = await Promise.all([
        http.fetchJson(context, pstats.queryLastEvent(instance, atfrom).url),
        http.fetchJson(context, pstats.queryEvents(instance, atfrom, now).url)]);
      if (!cutil.checkArray(fetched, 2)) throw new Error('Failed fetching player data');
      let results = {};
      [results.lastevent, results.events] = fetched;
      results = pstats.extractActivity(results);
      activityMap[scheme.range] = cutil.hasProp(results.results, instance) ? results.results[instance].players : [];
      activityMap[scheme.range].forEach(function(record) { record.alias = aliases.findByName(record.player); });
    }
  }
  schemes.reverse();  // Schemes higher in list have precedence over lower
  schemes.forEach(function(scheme) {  // Update role members based on reward scheme and activity
    const [recordedMembers, schemeRole] = [[], roleMap[scheme.snowflake]];
    const [schemeTop, schemePlayed] = [scheme.type === 'top', scheme.type === 'played'];
    let [inverted, schemeThreshold] = [false, cutil.rangeCodeToMillis(scheme.threshold)];
    if (schemeThreshold < 0) { [inverted, schemeThreshold] = [true, 0 - schemeThreshold]; }
    activityMap[scheme.range].forEach(function(record, index) {
      if (record.alias) {
        let give = !inverted && schemeTop && index < schemeThreshold;
        give ||= inverted && schemeTop && index >= schemeThreshold;
        give ||= !inverted && schemePlayed && record.uptime >= schemeThreshold;
        give ||= inverted && schemePlayed && record.uptime < schemeThreshold;
        give &&= scheme.action === 'give' && !schemeRole.members.includes(record.alias.snowflake);
        let take = !inverted && schemeTop && index >= schemeThreshold;
        take ||= inverted && schemeTop && index < schemeThreshold;
        take ||= !inverted && schemePlayed && record.uptime < schemeThreshold;
        take ||= inverted && schemePlayed && record.uptime >= schemeThreshold;
        take &&= scheme.action === 'take' && schemeRole.members.includes(record.alias.snowflake);
        if (give) {  // Add member to role if above threshold
          schemeRole.members.push(record.alias.snowflake);
        } else if (take) {  // Remove member from role if below threshold
          schemeRole.members = schemeRole.members.filter(function(member) { return member != record.alias.snowflake; });
        }
        recordedMembers.push(record.alias.snowflake);
      }
    });
    if (!inverted && scheme.action === 'take') {  // Remove member from role if not in activity
      schemeRole.members = schemeRole.members.filter(function(member) { return recordedMembers.includes(member); });
    }
  });
  for (const schemeRole of Object.values(roleMap)) {  // Apply roles based on new member list
    schemeRole.gives = schemeRole.members.filter(function(member) { return !schemeRole.orig.includes(member); });
    schemeRole.takes = schemeRole.orig.filter(function(member) { return !schemeRole.members.includes(member); });
    for (const [give, members] of [[false, schemeRole.takes], [true, schemeRole.gives]]) {
      for (const member of members) {
        await cutil.sleep(1000);
        let memberid = aliases.findByKey(member);
        memberid = memberid ? memberid.discordid : member;
        if (cutil.hasProp(membersMap, member)) {
          await roleModify(prelog, message.channel, memberid, membersMap[member], schemeRole.role, give);
        } else {
          message.channel.send(prelog + emojis.bang + ' Alias `@' + memberid + '` not found');
        }
      }
    }
  }
}
/* eslint-enable max-lines-per-function */
/* eslint-enable complexity */

export function reward({ context, aliases, rewards, instance, message, data }) {
  const cmd = data.length > 0 ? data[0] : 'list';
  if (cmd === 'list') {
    msgutil.sendText(message, rewards.listText());
  } else if (cmd === 'add' || cmd === 'give' || cmd === 'take') {
    if (cmd === 'add') { data = data.slice(1); }
    if (data.length < 5) return msgutil.reactUnknown(message);
    const [action, candidate, type, threshold, range] = data;
    const snowflake = util.toRoleId(candidate);
    if (!snowflake) return msgutil.reactError(message);
    message.guild.roles.fetch(snowflake)
      .then(function(role) {
        if (!role) return msgutil.reactError(message);
        if (!rewards.add(action, snowflake, role.name, type, threshold, range)) return msgutil.reactError(message);
        rewards.save();
        msgutil.reactSuccess(message);
      })
      .catch(function(error) { logger.error(error, message); });
  } else if (cmd === 'move') {
    if (data.length < 3) return msgutil.reactUnknown(message);
    if (!rewards.move(data[1], data[2])) return msgutil.reactError(message);
    rewards.save();
    msgutil.reactSuccess(message);
  } else if (cmd === 'remove') {
    if (data.length < 2) return msgutil.reactUnknown(message);
    if (!rewards.remove(data[1])) return msgutil.reactError(message);
    rewards.save();
    msgutil.reactSuccess(message);
  } else if (cmd === 'evaluate') {
    evaluateRewards(context, aliases, rewards, instance, message)
      .then(function() {
        msgutil.rmReacts(message, msgutil.reactSuccess, logger.error);
      })
      .catch(function(error) {
        msgutil.rmReacts(message, function() { logger.error(error, message); }, logger.error);
      });
  } else {
    msgutil.reactUnknown(message);
  }
}
