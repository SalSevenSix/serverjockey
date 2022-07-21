'use strict';

const commons = require('../commons.js');
const subs = require('../subs.js');

exports.startup = function(context, channel, instance, url) {
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
  c.send('TODO');
}
