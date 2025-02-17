/* eslint-disable max-lines */
const cutil = require('common/util/util');
const istats = require('common/activity/instance');
const pstats = require('common/activity/player');
const util = require('./util.js');
const logger = require('./logger.js');
const subs = require('./subs.js');
const fs = require('fs');
const fetch = require('node-fetch');

export function startServerEventLogging($) {
  const [context, channels, instance, url] = [$.context, $.channels, $.instance, $.url];
  if (!channels.server) return;
  let state = 'READY';
  let restartRequired = false;
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

export function startAllEventLogging($) {
  startServerEventLogging($);
  const [context, channels, aliases, instance, url] = [$.context, $.channels, $.aliases, $.instance, $.url];
  if (!channels.login && !channels.chat) return;
  new subs.Helper(context).daemon(url + '/players/subscribe', function(json) {
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
    return true;
  });
}

export function server($) {
  const [context, httptool, instance, message, data] = [$.context, $.httptool, $.instance, $.message, $.data];
  if (data.length === 0) {
    return httptool.doGet('/server', function(body) {
      let result = '```\nServer ' + instance + ' is ';
      if (!body.running) return result + 'DOWN\n```';
      result += body.state;
      if (body.uptime) { result += ' (' + cutil.humanDuration(body.uptime) + ')'; }
      result += '\n';
      const dtl = body.details;
      if (dtl.version) { result += 'Version:  ' + dtl.version + '\n'; }
      if (dtl.ip && dtl.port) { result += 'Connect:  ' + dtl.ip + ':' + dtl.port + '\n'; }
      if (dtl.ingametime) { result += 'Ingame:   ' + dtl.ingametime + '\n'; }
      if (dtl.map) { result += 'Map:      ' + dtl.map + '\n'; }
      if (dtl.restart) { result += 'SERVER RESTART REQUIRED\n'; }
      return result + '```';
    });
  }
  const signals = ['start', 'restart-immediately', 'restart-after-warnings', 'restart-on-empty', 'stop'];
  const upStates = ['START', 'STARTING', 'STARTED', 'STOPPING'];
  const downStates = ['READY', 'STOPPED', 'EXCEPTION'];
  let cmd = data[0].toLowerCase();
  if (cmd === 'restart') { cmd = signals[1]; }
  if (!signals.includes(cmd)) return util.reactUnknown(message);
  httptool.doPost('/server/' + cmd, { respond: true }, function(json) {
    let state = json.current.state;
    let targetUp = cmd === signals[0];
    if (targetUp && upStates.includes(state)) return util.reactError(message);
    if (!targetUp && downStates.includes(state)) return util.reactError(message);
    if ([signals[2], signals[3]].includes(cmd)) return util.reactSuccess(message);
    util.reactWait(message);
    targetUp ||= cmd === signals[1];
    new subs.Helper(context).poll(json.url, function(polldata) {
      if (state === polldata.state) return true;
      state = polldata.state;
      if (state === downStates[2]) return util.rmReacts(message, util.reactError, logger.error, false);
      if (targetUp && state === upStates[2]) return util.rmReacts(message, util.reactSuccess, logger.error, false);
      if (!targetUp && state === downStates[1]) return util.rmReacts(message, util.reactSuccess, logger.error, false);
      return true;
    });
  });
}

export function auto($) {
  const [httptool, instance, data] = [$.httptool, $.instance, $.data];
  if (data.length > 0) return httptool.doPost('', { auto: data[0] });
  const desc = ['Off', 'Auto Start', 'Auto Restart', 'Auto Start and Restart'];
  httptool.doGet('/server', function(body) {
    let result = '```\n' + instance;
    result += ' auto mode: ' + body.auto;
    result += ' (' + desc[body.auto] + ')\n```';
    return result;
  });
}

export function log($) {
  const [httptool, message] = [$.httptool, $.message];
  httptool.doGet('/log/tail', function(body) {
    if (!body) return message.channel.send('```\nNo log lines found\n```');
    const fname = 'log-' + message.id + '.text';
    const fpath = '/tmp/' + fname;
    fs.writeFile(fpath, body, function(error) {
      if (error) return logger.error(error);
      message.channel.send({ files: [{ attachment: fpath, name: fname }] })
        .finally(function() { fs.unlink(fpath, logger.error); });
    });
  });
}

export function getconfig($) {
  const [httptool, message, data] = [$.httptool, $.message, $.data];
  if (data.length === 0) return util.reactUnknown(message);
  httptool.doGet('/config/' + data[0], function(body) {
    const fname = data[0] + '-' + message.id + '.text';
    const fpath = '/tmp/' + fname;
    fs.writeFile(fpath, body, function(error) {
      if (error) return logger.error(error);
      message.channel.send({ files: [{ attachment: fpath, name: fname }] })
        .finally(function() { fs.unlink(fpath, logger.error); });
    });
  });
}

export function setconfig($) {
  const [httptool, message, data] = [$.httptool, $.message, $.data];
  const attachment = message.attachments.first();
  if (data.length === 0 || !attachment) return util.reactUnknown(message);
  fetch(attachment.url)
    .then(function(response) {
      if (!response.ok) throw new Error('Status: ' + response.status);
      return response.text();
    })
    .then(function(body) {
      if (body) { httptool.doPost('/config/' + data[0], body); }
    })
    .catch(function(error) {
      logger.error(error, message);
    });
}

export function deployment($) {
  const [httptool, message, data] = [$.httptool, $.message, [...$.data]];
  if (data.length === 0) return util.reactUnknown(message);
  const cmd = data.shift();
  let body = null;
  if (cmd === 'backup-runtime' || cmd === 'backup-world') {
    if (data.length > 0) { body = { prunehours: data[0] }; }
  } else if (cmd === 'install-runtime') {
    body = { wipe: false, validate: true };
    if (data.length > 0) { body.beta = data[0]; }
  }
  httptool.doPostToFile('/deployment/' + cmd, body);
}

export function send($) {
  const [httptool, message, data] = [$.httptool, $.message, $.data];
  if (data.length === 0) return util.reactUnknown(message);
  let line = message.content;
  line = line.slice(line.indexOf(' ')).trim();
  httptool.doPost('/console/send', { line: line }, function(text) {
    if (!text) return util.reactSuccess(message);
    message.channel.send('```\n' + text + '\n```');
  });
}

export function say($) {
  const [context, httptool, message, data] = [$.context, $.httptool, $.message, $.data];
  if (data.length === 0) return util.reactUnknown(message);
  let [name, line] = [message.member.user.tag, message.content];
  name = '@' + name.split('#')[0];
  line = line.slice(line.indexOf(' ')).trim();
  httptool.doPost(
    '/console/say', { player: name, text: line },
    function() { message.react('💬'); },
    context.config.PLAYER_ROLE
  );
}

export function players($) {
  const [httptool, aliases, instance] = [$.httptool, $.aliases, $.instance];
  httptool.doGet('/players', function(body) {
    let line = instance + ' players online: ' + body.length;
    if (body.length === 0) return '```\n' + line + '\n```';
    let result = [];
    result.push(line);
    const plen = Math.max(10, 2 + body.reduce(function(a, b) {
      return a.name.length > b.name.length ? a : b;
    }).name.length);
    body.forEach(function(entry) {
      line = entry.name.padEnd(plen);
      if (entry.steamid) { line = entry.steamid + ' ' + line; }
      else if (entry.steamid === '') { line = 'CONNECTED         ' + line; }
      if (cutil.hasProp(entry, 'uptime')) { line += cutil.humanDuration(entry.uptime, 2).padEnd(8); }
      else { line += '        '; }
      const playerAlias = aliases.findByName(entry.name);
      if (playerAlias) { line += ' @' + playerAlias.discordid; }
      result.push(line.trim());
    });
    result = util.chunkStringArray(result);
    result = result.map(function(text) {
      return '```\n' + text.join('\n') + '\n```';
    });
    return result;
  });
}

export function alias($) {
  const [context, aliases, message, data] = [$.context, $.aliases, $.message, [...$.data]];
  if (!util.checkHasRole(message, context.config.ADMIN_ROLE)) return;
  const cmd = data.length > 0 ? data.shift() : 'list';
  if (cmd === 'list') {
    util.chunkStringArray(aliases.listText()).forEach(function(chunk) {
      message.channel.send('```\n' + chunk.join('\n') + '\n```');
    });
  } else if (cmd === 'find') {
    if (data.length != 1) return util.reactUnknown(message);
    let text = {};
    [aliases.findByKey(data[0]), aliases.findByName(data[0])].forEach(function(record) {
      if (record) { text[record.snowflake] = record.toString(); }
    });
    text = Object.values(text);
    text = text.length > 0 ? text.join('\n') : 'No Alias Found';
    message.channel.send('```\n' + text + '\n```');
  } else if (cmd === 'add') {
    if (data.length != 2) return util.reactUnknown(message);
    const [snowflake, name] = [util.toSnowflake(data[0]), data[1]];
    if (!snowflake) return util.reactError(message);
    context.client.users.fetch(snowflake)
      .then(function(user) {
        const discordid = user.tag.replaceAll('#', '');
        if (!aliases.add(snowflake, discordid, name)) return util.reactError(message);
        aliases.save();
        util.reactSuccess(message);
      })
      .catch(function(error) { logger.error(error, message); });
  } else if (cmd === 'remove') {
    if (data.length != 1) return util.reactUnknown(message);
    if (!aliases.remove(data[0])) return util.reactError(message);
    aliases.save();
    util.reactSuccess(message);
  } else {
    util.reactUnknown(message);
  }
}

/* eslint-disable max-lines-per-function */
export async function evaluateRewards(context, httptool, aliases, rewards, instance, message) {
  const [now, baseurl, prelog] = [Date.now(), context.config.SERVER_URL, '`' + instance + '` '];
  let schemes = rewards.list();
  if (schemes.length === 0) return;
  util.reactWait(message);
  const [membersMap, roleMap, activityMap] = [{}, {}, {}];
  const allMembers = await message.guild.members.fetch();  // Fetch all members first to populate cache
  allMembers.forEach(function(member) { membersMap[member.id] = member; });
  for (const scheme of schemes) {  // Gather roles and thier members by snowflake
    if (!cutil.hasProp(roleMap, scheme.snowflake)) {
      await cutil.sleep(1000);
      const role = await message.guild.roles.fetch(scheme.snowflake);
      let schemeRole = null;
      if (role) {
        schemeRole = { role: role };
        schemeRole.orig = role.members.map(function(member) { return member.id; });
        schemeRole.members = [...schemeRole.orig];
      } else {
        message.channel.send(prelog + '❗ Role `@' + scheme.roleid + '` not found');
      }
      roleMap[scheme.snowflake] = schemeRole;
    }
  }
  for (const snowflake of Object.keys(roleMap)) {  // Delete invalid roles
    if (!roleMap[snowflake]) { delete roleMap[snowflake]; }
  }
  schemes = schemes.filter(function(scheme) {  // Remove schemes with invalid role
    return Object.keys(roleMap).includes(scheme.snowflake);
  });
  if (schemes.length === 0) return;
  for (const scheme of schemes) {  // Gather activity by range
    if (!cutil.hasProp(activityMap, scheme.range)) {
      const atfrom = now - cutil.rangeCodeToMillis(scheme.range);
      let results = {};
      [results.lastevent, results.events] = await Promise.all([
        httptool.getJson(pstats.queryLastEvent(instance, atfrom), baseurl),
        httptool.getJson(pstats.queryEvents(instance, atfrom, now), baseurl)]);
      results = pstats.extractActivity(results);
      activityMap[scheme.range] = cutil.hasProp(results.results, instance) ? results.results[instance].players : [];
      activityMap[scheme.range].forEach(function(record) { record.alias = aliases.findByName(record.player); });
    }
  }
  schemes.reverse();  // Schemes higher in list have precedence over lower
  schemes.forEach(function(scheme) {  // Update role members based on reward scheme and activity
    const [schemeRole, schemeThreshold] = [roleMap[scheme.snowflake], cutil.rangeCodeToMillis(scheme.threshold)];
    const recordedMembers = [];
    activityMap[scheme.range].forEach(function(record, index) {
      if (record.alias) {
        recordedMembers.push(record.alias.snowflake);
        let give = scheme.type === 'top' && index < schemeThreshold;
        give ||= scheme.type === 'played' && record.uptime >= schemeThreshold;
        give &&= scheme.action === 'give' && !schemeRole.members.includes(record.alias.snowflake);
        let take = scheme.type === 'top' && index >= schemeThreshold;
        take ||= scheme.type === 'played' && record.uptime < schemeThreshold;
        take &&= scheme.action === 'take' && schemeRole.members.includes(record.alias.snowflake);
        if (give) {  // Add member to role if above threshold
          schemeRole.members.push(record.alias.snowflake);
        } else if (take) {  // Remove member from role if below threshold
          schemeRole.members = schemeRole.members.filter(function(member) { return member != record.alias.snowflake; });
        }
      }
    });
    if (scheme.action === 'take') {  // Remove member from role if not in activity
      schemeRole.members = schemeRole.members.filter(function(member) { return recordedMembers.includes(member); });
    }
  });
  for (const schemeRole of Object.values(roleMap)) { // Apply roles based on new member list
    schemeRole.gives = schemeRole.members.filter(function(member) { return !schemeRole.orig.includes(member); });
    schemeRole.takes = schemeRole.orig.filter(function(member) { return !schemeRole.members.includes(member); });
    for (const roleChange of [[false, schemeRole.takes], [true, schemeRole.gives]]) {
      for (const member of roleChange[1]) {
        let memberid = aliases.findByKey(member);
        memberid = memberid ? memberid.discordid : member;
        await cutil.sleep(1000);
        if (!cutil.hasProp(membersMap, member)) {
          message.channel.send(prelog + '❗ Alias `@' + memberid + '` not found');
        } else if (roleChange[0]) {
          await membersMap[member].roles.add(schemeRole.role);
          message.channel.send(prelog + '🏅 `@' + memberid + '` 👍 `@' + schemeRole.role.name + '`');
        } else {
          await membersMap[member].roles.remove(schemeRole.role);
          message.channel.send(prelog + '🏅 `@' + memberid + '` 👎 `@' + schemeRole.role.name + '`');
        }
      }
    }
  }
}
/* eslint-enable max-lines-per-function */

export function reward($) {
  const [context, rewards, message, data] = [$.context, $.rewards, $.message, [...$.data]];
  if (!util.checkHasRole(message, context.config.ADMIN_ROLE)) return;
  const cmd = data.length > 0 ? data.shift() : 'list';
  if (cmd === 'list') {
    util.chunkStringArray(rewards.listText()).forEach(function(chunk) {
      message.channel.send('```\n' + chunk.join('\n') + '\n```');
    });
  } else if (cmd === 'add') {
    if (data.length != 5) return util.reactUnknown(message);
    const [action, candidate, type, threshold, range] = data;
    const snowflake = util.toSnowflake(candidate, '<@&');
    if (!snowflake) return util.reactError(message);
    message.guild.roles.fetch(snowflake)
      .then(function(role) {
        if (!rewards.add(action, snowflake, role.name, type, threshold, range)) return util.reactError(message);
        rewards.save();
        util.reactSuccess(message);
      })
      .catch(function(error) { logger.error(error, message); });
  } else if (cmd === 'move') {
    if (data.length != 2) return util.reactUnknown(message);
    if (!rewards.move(data[0], data[1])) return util.reactError(message);
    rewards.save();
    util.reactSuccess(message);
  } else if (cmd === 'remove') {
    if (data.length != 1) return util.reactUnknown(message);
    if (!rewards.remove(data[0])) return util.reactError(message);
    rewards.save();
    util.reactSuccess(message);
  } else if (cmd === 'evaluate') {
    evaluateRewards(context, $.httptool, $.aliases, rewards, $.instance, message)
      .then(function() {
        util.rmReacts(message, util.reactSuccess, logger.error);
      })
      .catch(function(error) {
        util.rmReacts(message, function() { logger.error(error, message); }, logger.error);
      });
  } else {
    util.reactUnknown(message);
  }
}

/* eslint-disable max-lines-per-function */
export function activity($) {
  const [context, httptool, aliases, instance, message, data] = [
    $.context, $.httptool, $.aliases, $.instance, $.message, $.data];
  if (!util.checkHasRole(message, context.config.ADMIN_ROLE)) return;
  const [baseurl, now] = [context.config.SERVER_URL, new Date()];
  let [tz, atto, atfrom, player, limit, format, query] = [null, null, null, null, 11, 'TEXT', 'player'];
  data.forEach(function(arg) {
    if (arg === 'instance') { query = arg; }
    else if (arg.startsWith('tz=')) { tz = arg.substring(3); }
    else if (arg.startsWith('player=')) { player = arg.substring(7); }
    else if (arg.startsWith('limit=')) { limit = parseInt(arg.substring(6), 10); }
    else if (arg.startsWith('format=')) { format = arg.substring(7).toUpperCase(); }
  });
  data.forEach(function(arg) {
    if (arg.startsWith('to=')) {
      atto = arg.substring(3);
      atto = ['LH', 'LD', 'LM', 'TM'].includes(atto)
        ? atto = cutil.presetDate(now, atto, tz).getTime()
        : atto = cutil.parseDateToMillis(atto, tz);
    } else if (arg.startsWith('from=')) {
      atfrom = arg.substring(5);
      atfrom = atfrom && ['d', 'h', 'm', 's'].includes(atfrom.slice(-1).toLowerCase())
        ? atfrom = 0 - cutil.rangeCodeToMillis(atfrom)
        : atfrom = cutil.parseDateToMillis(atfrom, tz);
    }
  });
  if (!atto) { atto = now.getTime(); }
  if (!atfrom) { atfrom = atto - 2592000000; }
  else if (atfrom < 0) { atfrom = atto + atfrom; }
  if (!tz) { tz = true; }
  let [results, text] = [{}, ['Invalid arguments']];
  if (query === 'instance') {
    Promise.all([
      httptool.getJson(istats.queryInstance(instance), baseurl),
      httptool.getJson(istats.queryLastEvent(instance, atfrom), baseurl),
      httptool.getJson(istats.queryEvents(instance, atfrom, atto), baseurl)])
      .then(function(promdata) {
        [results.instances, results.lastevent, results.events] = promdata;
        results = istats.extractActivity(results);
        results = { meta: results.meta, summary: results.results[0] };
        if (format === 'TEXT') {
          text = [];
          text.push('FROM ' + cutil.shortISODateTimeString(results.meta.atfrom, tz) +
            ' TO ' + cutil.shortISODateTimeString(results.meta.atto, tz) +
            ' (' + cutil.humanDuration(results.meta.atrange) + ')');
          text.push('CREATED ' + cutil.shortISODateTimeString(results.summary.created, tz));
          text.push('TOTAL sessions:' + results.summary.sessions +
            ' available:' + cutil.floatToPercent(results.summary.available) +
            ' uptime:' + cutil.humanDuration(results.summary.uptime));
        } else if (format === 'JSON') {
          text = [JSON.stringify(results)];
        }
        message.channel.send('```\n' + text.join('\n') + '\n```');
      });
  } else if (query === 'player') {
    Promise.all([
      httptool.getJson(pstats.queryLastEvent(instance, atfrom, player), baseurl),
      httptool.getJson(pstats.queryEvents(instance, atfrom, atto, player), baseurl)])
      .then(function(promdata) {
        [results.lastevent, results.events] = promdata;
        results = pstats.extractActivity(results);
        const instanceResults = cutil.hasProp(results.results, instance) ? results.results[instance] : null;
        results = { meta: results.meta,
          summary: instanceResults ? instanceResults.summary : null,
          players: instanceResults ? instanceResults.players : null };
        if (format === 'TEXT') {
          text = [];
          text.push('FROM ' + cutil.shortISODateTimeString(results.meta.atfrom, tz) +
            ' TO ' + cutil.shortISODateTimeString(results.meta.atto, tz) +
            ' (' + cutil.humanDuration(results.meta.atrange) + ')');
          if (instanceResults) {
            text.push('TOTAL unique:' + results.summary.unique +
              ' concurrent:' + results.summary.online.max +
              ' sessons:' + results.summary.total.sessions +
              ' played:' + cutil.humanDuration(results.summary.total.uptime));
            if (limit && !player) { results.players = pstats.compactPlayers(results.players, limit); }
            const plen = Math.max(10, 2 + results.players.reduce(function(a, b) {
              return a.player.length > b.player.length ? a : b;
            }).player.length);
            text.push(...results.players.map(function(record) {
              const playerAlias = aliases.findByName(record.player);
              let line = record.player.padEnd(plen) + cutil.humanDuration(record.uptime).padEnd(12);
              if (playerAlias) { line += ' @' + playerAlias.discordid; }
              return line.trim();
            }));
          } else {
            text.push('No player activity found');
          }
        } else if (format === 'JSON') {
          text = [JSON.stringify(results)];
        }
        util.chunkStringArray(text).forEach(function(chunk) {
          message.channel.send('```\n' + chunk.join('\n') + '\n```');
        });
      });
  }
}
/* eslint-enable max-lines-per-function */
/* eslint-enable max-lines */
