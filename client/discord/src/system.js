'use strict';

const util = require('./util.js');

exports.system = function($) {
  $.httptool.doGet('/system/info', function(info) {
    let result = '```';
    result += 'CPU    : ' + info.cpu.percent + '%\n';
    result += 'Memory : ' + util.humanFileSize(info.memory.used);
    result += ' / '       + util.humanFileSize(info.memory.total);
    result += ' ('        + info.memory.percent + '%)\n';
    result += 'Disk   : ' + util.humanFileSize(info.disk.used);
    result += ' / '       + util.humanFileSize(info.disk.total);
    result += ' ('        + info.disk.percent + '%)\n';
    result += 'Uptime : ' + util.humanDuration(info.uptime) + '```';
    return result;
  });
}

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
    $.context.instancesService.setInstance(body.identity);
    message.react('✅');
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
