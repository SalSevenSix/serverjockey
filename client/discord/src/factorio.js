'use strict';

const commons = require('./commons.js');
const subs = require('./subs.js');

exports.startup = function(context, channel, instance, url) {
  if (!channel) return;
  new subs.Helper(context).daemon(url + '/players/subscribe', function(json) {
    let result = '';
    if (json.event === 'join') { result += 'JOIN '; }
    if (json.event === 'leave') { result += 'LEAVE '; }
    result += json.name;
    result += ' (' + instance + ')';
    channel.send(result);
    return true;
  });
}

exports.server = commons.server
exports.getconfig = commons.getconfig
exports.setconfig = commons.setconfig
exports.deployment = commons.deployment
exports.players = commons.players

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
