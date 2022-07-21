'use strict';

const logger = require('../logger.js');
const util = require('../util.js');
const subs = require('../subs.js');
const fs = require('fs');
const fetch = require('node-fetch');

exports.startup = function(context, channel, instance, url) {
  new subs.Helper(context).daemon(url + '/players/subscribe', function(json) {
    let result = '';
    if (json.event === 'login') { result += 'LOGIN '; }
    if (json.event === 'logout') { result += 'LOGOUT '; }
    result += json.player.name;
    if (json.player.steamid != null) {
      result += ' [' + json.player.steamid + '] ' + instance;
    }
    channel.send(result);
    return true;
  });
}

exports.server = function($) {
  if ($.data.length === 1) {
    let cmd = $.data[0];
    $.httptool.doPost('/server/' + cmd, null, function(message, json) {
      if (cmd === 'daemon' || cmd === 'start' || cmd === 'restart') {
        message.react('⌛');
        let helper = new subs.Helper($.context);
        helper.subscribe($.httptool.baseurl + '/server/subscribe', function(pollUrl) {
          helper.poll(pollUrl, function(data) {
            if (data != null && data.running && data.state === 'STARTED') {
              message.reactions.removeAll()
                .then(function() { message.react('✅'); })
                .catch(logger.error);
              return false;
            }
            return true;
          });
        });
      } else if (cmd === 'delete') {
        $.context.instancesService.deleteInstance($.instance);
        message.react('✅');
      } else {
        message.react('✅');
      }
    });
    return;
  }
  $.httptool.doGet('/server', function(body) {
    let result = '```Server is ';
    if (!body.running) {
      result += 'DOWN```';
      return result;
    }
    result += body.state + '\n';
    let dtl = body.details;
    if (dtl.hasOwnProperty('version')) {
      result += 'Version:  ' + dtl.version + '\n';
    }
    if (dtl.hasOwnProperty('ip') && dtl.hasOwnProperty('port')) {
      result += 'Connect:  ' + dtl.ip + ':' + dtl.port + '\n';
    }
    if (dtl.hasOwnProperty('ingametime')) {
      result += 'Ingame:   ' + dtl.ingametime + '\n';
    }
    return result + '```';
  });
}

exports.config = function($) {
  let prefix = $.httptool.baseurl + '/config/';
  let result = prefix + 'jvm\n';
  result += prefix + 'options\n';
  result += prefix + 'ini\n';
  result += prefix + 'sandbox\n';
  result += prefix + 'spawnpoints\n';
  result += prefix + 'spawnregions\n';
  $.message.channel.send(result);
}

exports.getconfig = function($) {
  if ($.data.length < 1) return;
  $.httptool.doGet('/config/' + $.data[0], function(body) {
    let fname = $.data[0] + '-' + $.message.id + '.text';
    let fpath = '/tmp/' + fname;
    fs.writeFile(fpath, body, function(error) {
      if (error) return logger.error(error);
      $.message.channel.send({ files: [{ attachment: fpath, name: fname }] });
    });
  });
}

exports.setconfig = function($) {
  if ($.data.length < 1) return;
  if ($.message.attachments.length < 1) return;
  fetch($.message.attachments.first().url)
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

exports.log = function($) {
  $.message.channel.send($.httptool.baseurl + '/log/tail');
}

exports.world = function($) {
  let data = [...$.data];
  if (data.length < 1) return;
  let cmd = data.shift();
  let body = null;
  if (data.length > 0 && cmd === 'broadcast') {
    body = { message: data.join(' ') };
  }
  $.httptool.doPost('/world/' + cmd, body);
}

exports.deployment = function($) {
  let data = [...$.data];
  if (data.length < 1) return;
  let cmd = data.shift();
  let body = null;
  if (cmd === 'install-runtime') {
    body = { wipe: true, validate: true };
    if (data.length > 0) { body.beta = data[0]; }
  }
  $.httptool.doPostToFile('/deployment/' + cmd, body);
}

exports.players = function($) {
  $.httptool.doGet('/players', function(body) {
    let result = '```Players currently online: ' + body.length + '\n';
    for (let i = 0; i < body.length; i++) {
      if (body[i].steamid == null) {
        result += 'LOGGING IN        ';
      } else {
        result += body[i].steamid + ' ';
      }
      result += body[i].name + '\n';
    }
    return result + '```';
  });
}

exports.player = function($) {
  let data = [...$.data];
  if (data.length < 2) return;
  let name = util.stringToBase10(data.shift());
  let cmd = data.shift();
  let body = null;
  if (data.length > 0) {
    if (cmd === 'set-access-level') {
      body = { level: data[0] };
    } else if (cmd === 'tele-to') {
      body = { toplayer: util.stringToBase10(data[0]) };
    } else if (cmd === 'tele-at') {
      body = { location: data[0] };
    } else if (cmd === 'spawn-horde') {
      body = { count: data[0] };
    } else if (cmd === 'spawn-vehicle') {
      body = { module: data[0], item: data[1] };
    } else if (cmd === 'give-xp') {
      body = { skill: data[0], xp: data[1] };
    } else if (cmd === 'give-item') {
      body = { module: data[0], item: data[1] };
      if (data.length > 2) { body.count = data[2]; }
    }
  }
  $.httptool.doPost('/players/' + name + '/' + cmd, body);
}

exports.whitelist = function($) {
  let data = [...$.data];
  if (data.length < 2) return;
  let cmd = data.shift();
  let name = null;
  let body = null;
  if (cmd === 'add-name') {
    body = { player: util.stringToBase10(data[0]), password: data[1] };
    $.httptool.doPost('/whitelist/add', body);
  } else if (cmd === 'remove-name') {
    body = { player: util.stringToBase10(data[0]) };
    $.httptool.doPost('/whitelist/remove', body);
  } else if (cmd === 'add-id') {
    $.context.client.users.fetch(data[0], true, true)
      .then(function(user) {
        let pwd = Math.random().toString(16).substr(2, 8);
        name = user.tag.replace(/ /g, '').replace('#', '');
        logger.info('Add user: ' + data[0] + ' ' + name);
        body = { player: util.stringToBase10(name), password: pwd };
        if ($.httptool.doPost('/whitelist/add', body)) {
          user.send($.context.config.WHITELIST_DM.replace('${user}', name).replace('${pass}', pwd));
        }
      })
      .catch(function(error) {
        $.httptool.error(error, $.message);
      });
  } else if (cmd === 'remove-id') {
    $.context.client.users.fetch(data[0], true, true)
      .then(function(user) {
        name = user.tag.replace(/ /g, '').replace('#', '');
        logger.info('Remove user: ' + data[0] + ' ' + name);
        body = { player: util.stringToBase10(name) };
        $.httptool.doPost('/whitelist/remove', body);
      })
      .catch(function(error) {
        $.httptool.error(error, $.message);
      });
  }
}

exports.banlist = function($) {
  let data = [...$.data];
  if (data.length < 2) return;
  let cmd = data.shift() + '-id';
  let body = { steamid: data.shift() };
  $.httptool.doPost('/banlist/' + cmd, body);
}

exports.help = function($) {
  let x = $.context;
  let c = $.message.channel;
  if ($.data.length === 0) {
    let s = '```PROJECT ZOMBOID COMMANDS\n' + x.config.CMD_PREFIX;
    c.send(s + x.staticData.projectzomboid.help1.join('\n' + x.config.CMD_PREFIX) + '```');
    c.send(s + x.staticData.projectzomboid.help2.join('\n' + x.config.CMD_PREFIX) + '```');
    c.send(s + x.staticData.projectzomboid.help3.join('\n' + x.config.CMD_PREFIX) + '```');
    return;
  }
  let query = $.data.join('').replaceAll('-', '');
  if (x.staticData.projectzomboid.hasOwnProperty(query)) {
    c.send(x.staticData.projectzomboid[query].join('\n'));
  } else {
    c.send('No more help available.');
  }
}
