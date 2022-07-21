'use strict';

const util = require('./util.js');

exports.instances = function($) {
  $.message.channel.send($.context.instancesService.getInstancesText());
}

exports.use = function($) {
  if (!util.checkAdmin($.message, $.context.config.ADMIN_ROLE)) return;
  if ($.data.length > 0) {
    $.context.instancesService.useInstance($.data[0]);
    $.message.channel.send($.context.instancesService.getInstancesText());
  }
}

exports.create = function($) {
  if ($.data.length < 2) return;
  let body = { identity: $.data[0], module: $.data[1] };
  $.httptool.doPost('/instances', body, function(message, json) {
    $.context.instancesService.createInstance(body);
    message.channel.send($.context.instancesService.getInstancesText());
  });
}

exports.shutdown = function($) {
  $.httptool.doPost('/system/shutdown');
}

exports.help = function($) {
  let result = '```SYSTEM COMMANDS\n' + $.context.config.CMD_PREFIX;
  result += $.context.staticData.system.help.join('\n' + $.context.config.CMD_PREFIX);
  $.message.channel.send(result + '```');
}
