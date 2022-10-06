'use strict';

const commons = require('../commons.js');

exports.startup = commons.startupSubscribePlayers;
exports.server = commons.server;
exports.getconfig = commons.getconfig;
exports.setconfig = commons.setconfig;
exports.deployment = commons.deployment;
exports.players = commons.players;

exports.help = function($) {
  let c = $.message.channel;
  if ($.data.length > 0) {
    c.send('No more help available.');
    return;
  }
  let x = $.context;
  let s = '```FACTORIO COMMANDS\n' + x.config.CMD_PREFIX;
  c.send(s + x.staticData.factorio.help1.join('\n' + x.config.CMD_PREFIX) + '```');
  return;
}
