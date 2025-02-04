/* eslint-disable max-lines */
const cutil = require('common/util/util');
const istats = require('common/activity/instance');
const pstats = require('common/activity/player');
const util = require('./util.js');
const logger = require('./logger.js');
const subs = require('./subs.js');
const fs = require('fs');
const fetch = require('node-fetch');

exports.helpText = {
  activity: [
    'Activity Reporting. Provide the following query parameters...', '```',
    'instance        : Report instance activity instead of player activity',
    'from={date}     : From date in ISO 8601 format YYYY-MM-DDThh:mm:ss',
    '                  or days {n}D prior, or hours {n}H prior to date',
    'to={date}       : To date in ISO 8601 format YYYY-MM-DDThh:mm:ss',
    '                  or preset "LD" Last Day, "LM" Last Month, "TD" This Month',
    'tz={timezone}   : Timezone as ±{hh} or ±{hh}:{mm} default is server tz',
    '"player={name}" : Specify a player by name to report on',
    'limit={rows}    : Limit number of players rows returned',
    'format={type}   : Provide results in "TEXT" or "JSON" format',
    '```', 'Examples...',
    'a) get instance activity between specific dates in timezone GMT +7',
    '`!activity instance from=2024-08-01T00:00:00 to=2024-09-01T00:00:00 tz=+7`',
    'b) get the top 3 players from last 7 days ending yesterday',
    '`!activity from=7D to=LD limit=4`',
    'c) get player activity by name in json format',
    '`!activity "player=Mr Tee" format=JSON`'
  ]
};

exports.startServerEventLogging = function(context, channels, instance, url) {
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
};

exports.startAllEventLogging = function(context, channels, instance, url) {
  exports.startServerEventLogging(context, channels, instance, url);
  if (!channels.login && !channels.chat) return;
  new subs.Helper(context).daemon(url + '/players/subscribe', function(json) {
    if (json.event === 'CHAT') {
      if (!channels.chat) return true;
      channels.chat.send('`' + instance + '` 💬 ' + json.player.name + ': ' + json.text);
      return true;
    }
    if (!channels.login) return true;
    let result = null;
    if (json.event === 'LOGIN') { result = ' 🟢 '; }
    else if (json.event === 'LOGOUT') { result = ' 🔴 '; }
    else if (json.event === 'DEATH') { result = ' 💀 '; }
    if (!result) return true;
    result = '`' + instance + '`' + result + json.player.name;
    if (json.text) { result += ' [' + json.text + ']'; }
    if (json.player.steamid) { result += ' [' + json.player.steamid + ']'; }
    channels.login.send(result);
    return true;
  });
};

exports.sendHelp = function($, helpText) {
  if ($.data.length === 0) {
    const cmd = $.context.config.CMD_PREFIX;
    let header = '```\n' + helpText.title + '\n' + cmd;
    let index = 1;
    while (cutil.hasProp(helpText, 'help' + index)) {
      $.message.channel.send(header + helpText['help' + index].join('\n' + cmd) + '\n```');
      if (index === 1) { header = '```\n' + cmd; }
      index += 1;
    }
    return;
  }
  const query = $.data.join('').replaceAll('-', '');
  if (query === 'title' || !cutil.hasProp(helpText, query)) {
    $.message.channel.send('No more help available.');
  } else if (cutil.isString(helpText[query])) {
    $.httptool.doGet(helpText[query], function(body) { return '```\n' + body + '\n```'; });
  } else {
    $.message.channel.send(helpText[query].join('\n'));
  }
};

exports.server = function($) {
  if ($.data.length === 0) {
    $.httptool.doGet('/server', function(body) {
      let result = '```\nServer ' + $.instance + ' is ';
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
    return;
  }
  const signals = ['start', 'restart-immediately', 'restart-after-warnings', 'restart-on-empty', 'stop'];
  const upStates = ['START', 'STARTING', 'STARTED', 'STOPPING'];
  const downStates = ['READY', 'STOPPED', 'EXCEPTION'];
  let cmd = $.data[0].toLowerCase();
  if (cmd === 'restart') { cmd = signals[1]; }
  if (!signals.includes(cmd)) return util.reactUnknown($.message);
  $.httptool.doPost('/server/' + cmd, { respond: true }, function(json) {
    let state = json.current.state;
    let targetUp = cmd === signals[0];
    if (targetUp && upStates.includes(state)) return util.reactError($.message);
    if (!targetUp && downStates.includes(state)) return util.reactError($.message);
    if ([signals[2], signals[3]].includes(cmd)) return util.reactSuccess($.message);
    util.reactWait($.message);
    targetUp ||= cmd === signals[1];
    new subs.Helper($.context).poll(json.url, function(data) {
      if (state === data.state) return true;
      state = data.state;
      if (state === downStates[2]) return util.rmReacts($.message, util.reactError, logger.error, false);
      if (targetUp && state === upStates[2]) return util.rmReacts($.message, util.reactSuccess, logger.error, false);
      if (!targetUp && state === downStates[1]) return util.rmReacts($.message, util.reactSuccess, logger.error, false);
      return true;
    });
  });
};

exports.auto = function($) {
  if ($.data.length > 0) {
    $.httptool.doPost('', { auto: $.data[0] });
    return;
  }
  const desc = ['Off', 'Auto Start', 'Auto Restart', 'Auto Start and Restart'];
  $.httptool.doGet('/server', function(body) {
    let result = '```\n' + $.instance;
    result += ' auto mode: ' + body.auto;
    result += ' (' + desc[body.auto] + ')\n```';
    return result;
  });
};

exports.log = function($) {
  $.httptool.doGet('/log/tail', function(body) {
    if (!body) {
      $.message.channel.send('```\nNo log lines found\n```');
      return;
    }
    const fname = 'log-' + $.message.id + '.text';
    const fpath = '/tmp/' + fname;
    fs.writeFile(fpath, body, function(error) {
      if (error) return logger.error(error);
      $.message.channel.send({ files: [{ attachment: fpath, name: fname }] })
        .finally(function() { fs.unlink(fpath, logger.error); });
    });
  });
};

exports.getconfig = function($) {
  if ($.data.length === 0) return util.reactUnknown($.message);
  $.httptool.doGet('/config/' + $.data[0], function(body) {
    const fname = $.data[0] + '-' + $.message.id + '.text';
    const fpath = '/tmp/' + fname;
    fs.writeFile(fpath, body, function(error) {
      if (error) return logger.error(error);
      $.message.channel.send({ files: [{ attachment: fpath, name: fname }] })
        .finally(function() { fs.unlink(fpath, logger.error); });
    });
  });
};

exports.setconfig = function($) {
  const attachment = $.message.attachments.first();
  if ($.data.length === 0 || !attachment) return util.reactUnknown($.message);
  fetch(attachment.url)
    .then(function(response) {
      if (!response.ok) throw new Error('Status: ' + response.status);
      return response.text();
    })
    .then(function(body) {
      if (body) { $.httptool.doPost('/config/' + $.data[0], body); }
    })
    .catch(function(error) {
      logger.error(error, $.message);
    });
};

exports.deployment = function($) {
  const data = [...$.data];
  if (data.length === 0) return util.reactUnknown($.message);
  const cmd = data.shift();
  let body = null;
  if (cmd === 'backup-runtime' || cmd === 'backup-world') {
    if (data.length > 0) { body = { prunehours: data[0] }; }
  } else if (cmd === 'install-runtime') {
    body = { wipe: false, validate: true };
    if (data.length > 0) { body.beta = data[0]; }
  }
  $.httptool.doPostToFile('/deployment/' + cmd, body);
};

exports.send = function($) {
  if ($.data.length === 0) return util.reactUnknown($.message);
  let data = $.message.content;
  data = data.slice(data.indexOf(' ')).trim();
  $.httptool.doPost('/console/send', { line: data }, function(text) {
    if (!text) return util.reactSuccess($.message);
    $.message.channel.send('```\n' + text + '\n```');
  });
};

exports.say = function($) {
  if ($.data.length === 0) return util.reactUnknown($.message);
  let [name, data] = [$.message.member.user.tag, $.message.content];
  name = '@' + name.split('#')[0];
  data = data.slice(data.indexOf(' ')).trim();
  $.httptool.doPost(
    '/console/say', { player: name, text: data },
    function() { $.message.react('💬'); },
    $.context.config.PLAYER_ROLE
  );
};

exports.players = function($) {
  $.httptool.doGet('/players', function(body) {
    const [result, nosteamid] = [[], 'CONNECTED         '];
    let line = $.instance + ' players online: ' + body.length;
    let [chars, chunk] = [line.length, [line]];
    if (body.length > 0) {
      let maxlen = body.reduce(function(a, b) { return a.name.length > b.name.length ? a : b; }).name.length;
      if (body[0].steamid != null) { maxlen += nosteamid.length; }
      for (let i = 0; i < body.length; i++) {
        if (body[i].steamid == null) {
          line = body[i].name;
        } else {
          line = body[i].steamid === '' ? nosteamid : body[i].steamid + ' ';
          line += body[i].name;
        }
        if (cutil.hasProp(body[i], 'uptime')) {
          line = line.padEnd(maxlen + 3);
          line += cutil.humanDuration(body[i].uptime, 2);
        }
        chunk.push(line);
        chars += line.length + 1;
        if (chars > 1600) {  // Discord message limit is 2000 characters
          result.push('```\n' + chunk.join('\n') + '\n```');
          [chars, chunk] = [0, []];
        }
      }
    }
    if (chunk.length > 0) {
      result.push('```\n' + chunk.join('\n') + '\n```');
    }
    return result;
  });
};

/* eslint-disable max-lines-per-function */
exports.activity = function($) {
  const [httptool, instance, message] = [$.httptool, $.instance, $.message];
  const [baseurl, now] = [$.context.config.SERVER_URL, new Date()];
  let [tz, atto, atfrom, player, limit, format, query] = [null, null, null, null, 11, 'TEXT', 'player'];
  $.data.forEach(function(arg) {
    if (arg === 'instance') { query = arg; }
    else if (arg.startsWith('tz=')) { tz = arg.substring(3); }
    else if (arg.startsWith('player=')) { player = arg.substring(7); }
    else if (arg.startsWith('limit=')) { limit = parseInt(arg.substring(6), 10); }
    else if (arg.startsWith('format=')) { format = arg.substring(7).toUpperCase(); }
  });
  $.data.forEach(function(arg) {
    if (arg.startsWith('to=')) {
      atto = arg.substring(3);
      if (['LH', 'LD', 'LM', 'TM'].includes(atto)) { atto = cutil.presetDate(now, atto, tz).getTime(); }
      else { atto = cutil.parseDateToMillis(atto, tz); }
    } else if (arg.startsWith('from=')) {
      atfrom = arg.substring(5);
      if (atfrom.endsWith('d') || atfrom.endsWith('D')) { atfrom = parseInt(atfrom.slice(0, -1), 10) * -86400000; }
      else if (atfrom.endsWith('h') || atfrom.endsWith('H')) { atfrom = parseInt(atfrom.slice(0, -1), 10) * -3600000; }
      else { atfrom = cutil.parseDateToMillis(atfrom, tz); }
    }
  });
  if (!atto) { atto = now.getTime(); }
  if (!atfrom) { atfrom = atto - 2592000000; }
  else if (atfrom < 0) { atfrom = atto + atfrom; }
  if (!tz) { tz = true; }
  let [results, text] = [{}, 'invalid arguments'];
  if (query === 'instance') {
    Promise.all([httptool.getJson(istats.queryInstance(instance), baseurl),
      httptool.getJson(istats.queryLastEvent(instance, atfrom), baseurl),
      httptool.getJson(istats.queryEvents(instance, atfrom, atto), baseurl)])
      .then(function(data) {
        [results.instances, results.lastevent, results.events] = data;
        results = istats.extractActivity(results);
        results = { meta: results.meta, summary: results.results[0] };
        if (format === 'TEXT') {
          text = 'FROM ' + cutil.shortISODateTimeString(results.meta.atfrom, tz);
          text += ' TO ' + cutil.shortISODateTimeString(results.meta.atto, tz);
          text += ' (' + cutil.humanDuration(results.meta.atrange) + ')\n';
          text += 'CREATED ' + cutil.shortISODateTimeString(results.summary.created, tz) + '\n';
          text += 'TOTAL sessions:' + results.summary.sessions;
          text += ' available:' + cutil.floatToPercent(results.summary.available);
          text += ' uptime: ' + cutil.humanDuration(results.summary.uptime);
        } else if (format === 'JSON') {
          text = JSON.stringify(results);
        }
        message.channel.send('```\n' + text + '\n```');
      });
  } else if (query === 'player') {
    Promise.all([httptool.getJson(pstats.queryLastEvent(instance, atfrom, player), baseurl),
      httptool.getJson(pstats.queryEvents(instance, atfrom, atto, player), baseurl)])
      .then(function(data) {
        [results.lastevent, results.events] = data;
        results = pstats.extractActivity(results);
        results = { meta: results.meta, summary: results.results[instance].summary,
          players: results.results[instance].players };
        if (limit && !player) { results.players = pstats.compactPlayers(results.players, limit); }
        if (format === 'TEXT') {
          text = 'FROM ' + cutil.shortISODateTimeString(results.meta.atfrom, tz);
          text += ' TO ' + cutil.shortISODateTimeString(results.meta.atto, tz);
          text += ' (' + cutil.humanDuration(results.meta.atrange) + ')\n';
          text += 'TOTAL unique:' + results.summary.unique + ' concurrent:' + results.summary.online.max;
          text += ' sessons:' + results.summary.total.sessions;
          text += ' played: ' + cutil.humanDuration(results.summary.total.uptime) + '\n';
          const plen = Math.max(8, results.players.reduce(function(a, b) {
            return a.player.length > b.player.length ? a : b;
          }).player.length + 3);
          results.players = results.players.map(function(record) {
            return record.player.padEnd(plen) + cutil.humanDuration(record.uptime);
          });
          text += results.players.join('\n');
        } else if (format === 'JSON') {
          text = JSON.stringify(results);
        }
        message.channel.send('```\n' + text + '\n```');
      });
  }
};
/* eslint-enable max-lines-per-function */
/* eslint-enable max-lines */
