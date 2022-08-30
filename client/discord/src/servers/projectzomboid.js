'use strict';

const logger = require('../logger.js');
const util = require('../util.js');
const subs = require('../subs.js');
const commons = require('../commons.js');

exports.startup = function(context, channel, instance, url) {
  if (!channel) return;
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

exports.server = commons.server
exports.getconfig = commons.getconfig
exports.setconfig = commons.setconfig
exports.deployment = commons.deployment
exports.players = commons.players

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

exports.player = function($) {
  let data = [...$.data];
  if (data.length < 2) return;
  let name = util.urlSafeB64encode(data.shift());
  let cmd = data.shift();
  let body = null;
  if (data.length > 0) {
    if (cmd === 'set-access-level') {
      body = { level: data[0] };
    } else if (cmd === 'tele-to') {
      body = { toplayer: util.urlSafeB64encode(data[0]) };
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
    body = { player: util.urlSafeB64encode(data[0]), password: data[1] };
    $.httptool.doPost('/whitelist/add', body);
  } else if (cmd === 'remove-name') {
    body = { player: util.urlSafeB64encode(data[0]) };
    $.httptool.doPost('/whitelist/remove', body);
  } else if (cmd === 'add-id') {
    $.context.client.users.fetch(data[0], true, true)
      .then(function(user) {
        let pwd = Math.random().toString(16).substr(2, 8);
        name = user.tag.replace(/ /g, '').replace('#', '');
        logger.info('Add user: ' + data[0] + ' ' + name);
        body = { player: util.urlSafeB64encode(name), password: pwd };
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
        body = { player: util.urlSafeB64encode(name) };
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
