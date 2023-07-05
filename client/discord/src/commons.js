'use strict';

const logger = require('./logger.js');
const util = require('./util.js');
const subs = require('./subs.js');
const fs = require('fs');
const fetch = require('node-fetch');

exports.startupEventLogging = function(context, channels, instance, url) {
  let helper = new subs.Helper(context);
  let lastState = 'READY';
  let restartRequired = false;
  helper.daemon(url + '/server/subscribe', function(json) {
    if (!json.state) return true;  // ignore no state
    if (json.state === 'START') return true;  // ignore transient state
    if (!restartRequired && json.details.restart) {
      if (channels.server) { channels.server.send('`' + instance + '` 🔄 restart required'); }
      restartRequired = true;
      return true;
    }
    if (json.state === lastState) return true;  // ignore duplicates
    if (json.state === 'STARTED') { restartRequired = false; }
    lastState = json.state;
    if (channels.server) { channels.server.send('`' + instance + '` 📡 ' + json.state); }
    return true;
  });
  helper.daemon(url + '/players/subscribe', function(json) {
    if (json.event === 'chat') {
      if (channels.chat) { channels.chat.send('`' + instance + '` 💬 ' + json.player.name + ': ' + json.text); }
      return true;
    }
    let action = null;
    if (json.event === 'login') { action = ' ➡️ '; }
    if (json.event === 'logout') { action = ' ⬅️ '; }
    if (!action) return true;
    let result = '`' + instance + '`' + action + json.player.name;
    if (json.player.steamid) {
      result += ' [' + json.player.steamid + ']';
    }
    if (channels.login) { channels.login.send(result); }
    return true;
  });
}

exports.sendHelp = function($, helpText) {
  let channel = $.message.channel;
  if ($.data.length === 0) {
    let cmd = $.context.config.CMD_PREFIX;
    let header = '```\n' + helpText.title + '\n' + cmd;
    let index = 1;
    while (helpText.hasOwnProperty('help' + index)) {
      channel.send(header + helpText['help' + index].join('\n' + cmd) + '\n```');
      if (index === 1) { header = '```\n' + cmd; }
      index += 1;
    }
    return;
  }
  let query = $.data.join('').replaceAll('-', '');
  if (!helpText.hasOwnProperty(query)) {
    channel.send('No more help available.');
    return;
  }
  if (util.isString(helpText[query])) {
    $.httptool.doGet(helpText[query], function(body) { return '```\n' + body + '\n```'; });
  } else {
    channel.send(helpText[query].join('\n'));
  }
}

exports.server = function($) {
  if ($.data.length === 0) {
    $.httptool.doGet('/server', function(body) {
      let result = '```\nServer ' + $.instance + ' is ';
      if (!body.running) {
        result += 'DOWN\n```';
        return result;
      }
      result += body.state;
      if (body.uptime) { result += ' (' + util.humanDuration(body.uptime) + ')'; }
      result += '\n';
      let dtl = body.details;
      if (dtl.version) { result += 'Version:  ' + dtl.version + '\n'; }
      if (dtl.ip && dtl.port) { result += 'Connect:  ' + dtl.ip + ':' + dtl.port + '\n'; }
      if (dtl.ingametime) { result += 'Ingame:   ' + dtl.ingametime + '\n'; }
      if (dtl.restart) { result += 'SERVER RESTART REQUIRED\n'; }
      return result + '```';
    });
    return;
  }
  let cmd = $.data[0];
  if (cmd === 'delete') {  // Blocking this. Webapp and CLI only.
    $.message.react('⛔');
    return;
  }
  $.httptool.doPost('/server/' + cmd, { respond: true }, function(json) {
    let currentState = json.current.state;
    let targetUp = (cmd === 'start' || cmd === 'daemon');
    if (targetUp && ['START', 'STARTING', 'STARTED', 'STOPPING'].includes(currentState)) {
      $.message.react('⛔');
      return;
    }
    if (!targetUp && ['READY', 'STOPPED', 'EXCEPTION'].includes(currentState)) {
      $.message.react('⛔');
      return;
    }
    $.message.react('⌛');
    targetUp = targetUp || cmd === 'restart';
    new subs.Helper($.context).poll(json.url, function(data) {
      if (data.state === currentState) return true;
      currentState = data.state;
      if (currentState === 'EXCEPTION') {
        $.message.reactions.removeAll().then(function() { $.message.react('⛔'); }).catch(logger.error);
        return false;
      }
      if (targetUp && currentState === 'STARTED') {
        $.message.reactions.removeAll().then(function() { $.message.react('✅'); }).catch(logger.error);
        return false;
      }
      if (!targetUp && currentState === 'STOPPED') {
        $.message.reactions.removeAll().then(function() { $.message.react('✅'); }).catch(logger.error);
        return false;
      }
      return true;
    });
  });
}

exports.auto = function($) {
  if ($.data.length > 0) {
    $.httptool.doPost('', { auto: $.data[0] });
    return;
  }
  let desc = ['Off', 'Auto Start', 'Auto Restart', 'Auto Start and Restart'];
  $.httptool.doGet('/server', function(body) {
    let result = '```\n' + $.instance;
    result += ' auto mode: ' + body.auto;
    result += ' (' + desc[body.auto] + ')\n```';
    return result;
  });
}

exports.log = function($) {
  $.httptool.doGet('/log/tail', function(body) {
    if (!body) {
      $.message.channel.send('```\nNo log lines found\n```');
      return;
    }
    let fname = 'log-' + $.message.id + '.text';
    let fpath = '/tmp/' + fname;
    fs.writeFile(fpath, body, function(error) {
      if (error) return logger.error(error);
      $.message.channel.send({ files: [{ attachment: fpath, name: fname }] })
        .finally(function() { fs.unlink(fpath, logger.error); });
    });
  });
}

exports.getconfig = function($) {
  if ($.data.length === 0) {
    $.message.react('❓');
    return;
  }
  $.httptool.doGet('/config/' + $.data[0], function(body) {
    let fname = $.data[0] + '-' + $.message.id + '.text';
    let fpath = '/tmp/' + fname;
    fs.writeFile(fpath, body, function(error) {
      if (error) return logger.error(error);
      $.message.channel.send({ files: [{ attachment: fpath, name: fname }] })
        .finally(function() { fs.unlink(fpath, logger.error); });
    });
  });
}

exports.setconfig = function($) {
  let attachment = $.message.attachments.first();
  if ($.data.length === 0 || !attachment) {
    $.message.react('❓');
    return;
  }
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
      $.httptool.error(error, $.message);
    });
}

exports.deployment = function($) {
  let data = [...$.data];
  if (data.length === 0) {
    $.message.react('❓');
    return;
  }
  let cmd = data.shift();
  let body = null;
  if (cmd === 'backup-runtime' || cmd === 'backup-world') {
    if (data.length > 0) { body = { prunehours: data[0] }; }
  }
  if (cmd === 'install-runtime') {
    body = { wipe: false, validate: true };
    if (data.length > 0) { body.beta = data[0]; }
  }
  $.httptool.doPostToFile('/deployment/' + cmd, body);
}

exports.send = function($) {
  if ($.data.length === 0) {
    $.message.react('❓');
    return;
  }
  let data = $.message.content;
  data = data.slice(data.indexOf(' ')).trim();
  $.httptool.doPost('/console/send', { line: data }, function(text) {
    if (text) {
      $.message.channel.send('```\n' + text + '\n```');
    } else {
      $.message.react('✅');
    }
  });
}

exports.say = function($) {
  if ($.data.length === 0) {
    $.message.react('❓');
    return;
  }
  let name = $.message.member.user.tag;
  name = '@' + name.split('#')[0];
  let data = $.message.content;
  data = data.slice(data.indexOf(' ')).trim();
  $.httptool.doPost(
    '/console/say', { player: name, text: data },
    function(x) { $.message.react('💬'); },
    $.context.config.CHAT_ROLE);
}

exports.players = function($) {
  $.httptool.doGet('/players', function(body) {
    let line = $.instance + ' players online: ' + body.length;
    let chars = line.length;
    let chunk = [line];
    let result = [];
    for (let i = 0; i < body.length; i++) {
      if (body[i].hasOwnProperty('steamid')) {
        line = 'LOGGING IN       ';
        if (body[i].steamid != null) { line = body[i].steamid; }
        line += ' ' + body[i].name;
      } else {
        line = body[i].name;
      }
      chunk.push(line);
      chars += line.length;
      if (chars > 1600) {
        result.push('```\n' + chunk.join('\n') + '\n```');
        chars = 0;
        chunk = [];
      }
    }
    if (chunk.length > 0) {
      result.push('```\n' + chunk.join('\n') + '\n```');
    }
    return result;
  });
}
