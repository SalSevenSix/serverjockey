'use strict';

const logger = require('../logger.js');
const util = require('../util.js');
const commons = require('../commons.js');

exports.startup = commons.startupSubscribePlayers;
exports.server = commons.server;
exports.getconfig = commons.getconfig;
exports.setconfig = commons.setconfig;
exports.deployment = commons.deployment;
exports.players = commons.players;

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
      body = { toplayer: data[0] };
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
  if (cmd === 'add-name') {
    $.httptool.doPost('/whitelist/add', { player: data[0], password: data[1] });
  } else if (cmd === 'remove-name') {
    $.httptool.doPost('/whitelist/remove', { player: data[0] });
  } else if (cmd === 'add-id') {
    $.context.client.users.fetch(data[0], true, true)
      .then(function(user) {
        let pwd = Math.random().toString(16).substr(2, 8);
        let name = user.tag.replaceAll(' ', '').replaceAll('#', '');
        logger.info('Add user: ' + data[0] + ' ' + name);
        if ($.httptool.doPost('/whitelist/add', { player: name, password: pwd })) {
          user.send($.context.config.WHITELIST_DM.replace('${user}', name).replace('${pass}', pwd));
        }
      })
      .catch(function(error) {
        $.httptool.error(error, $.message);
      });
  } else if (cmd === 'remove-id') {
    $.context.client.users.fetch(data[0], true, true)
      .then(function(user) {
        let name = user.tag.replaceAll(' ', '').replaceAll('#', '');
        logger.info('Remove user: ' + data[0] + ' ' + name);
        $.httptool.doPost('/whitelist/remove', { player: name });
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
