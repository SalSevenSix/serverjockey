const logger = require('./logger.js');
const util = require('./util.js');
const subs = require('./subs.js');
const fs = require('fs');
const fetch = require('node-fetch');

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
    if (json.event === 'DEATH') { result = ' 💀 '; }
    if (json.event === 'LOGOUT') { result = ' 🔴 '; }
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
    while (util.hasProp(helpText, 'help' + index)) {
      $.message.channel.send(header + helpText['help' + index].join('\n' + cmd) + '\n```');
      if (index === 1) { header = '```\n' + cmd; }
      index += 1;
    }
    return;
  }
  const query = $.data.join('').replaceAll('-', '');
  if (query === 'title' || !util.hasProp(helpText, query)) {
    $.message.channel.send('No more help available.');
  } else if (util.isString(helpText[query])) {
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
      if (body.uptime) { result += ' (' + util.humanDuration(body.uptime) + ')'; }
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
      if (body == null) return;
      $.httptool.doPost('/config/' + $.data[0], body);
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
  let name = $.message.member.user.tag;
  name = '@' + name.split('#')[0];
  let data = $.message.content;
  data = data.slice(data.indexOf(' ')).trim();
  $.httptool.doPost(
    '/console/say', { player: name, text: data },
    function() { $.message.react('💬'); },
    $.context.config.PLAYER_ROLE
  );
};

exports.players = function($) {
  $.httptool.doGet('/players', function(body) {
    const result = [];
    const nosteamid = 'CONNECTED         ';
    let line = $.instance + ' players online: ' + body.length;
    let chars = line.length;
    let chunk = [line];
    let maxlength = 0;
    if (body.length > 0) {
      for (let i = 0; i < body.length; i++) {
        if (body[i].name.length > maxlength) { maxlength = body[i].name.length; }
      }
      if (body[0].steamid != null) { maxlength += nosteamid.length; }
      for (let i = 0; i < body.length; i++) {
        if (body[i].steamid == null) {
          line = body[i].name;
        } else {
          line = body[i].steamid === '' ? nosteamid : body[i].steamid + ' ';
          line += body[i].name;
        }
        if (util.hasProp(body[i], 'uptime')) {
          line = line.padEnd(maxlength + 3);
          line += util.humanDuration(body[i].uptime, 2);
        }
        chunk.push(line);
        chars += line.length + 1;
        if (chars > 1600) {  // Discord message limit is 2000 characters
          result.push('```\n' + chunk.join('\n') + '\n```');
          chars = 0;
          chunk = [];
        }
      }
    }
    if (chunk.length > 0) {
      result.push('```\n' + chunk.join('\n') + '\n```');
    }
    return result;
  });
};
