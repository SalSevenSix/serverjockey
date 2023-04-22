'use strict';

const util = require('./util.js');
const helpText = {
  help: [
    'help {command} {action}    : Show help',
    'system                     : Show system information',
    'instances                  : Show server instances list',
    'use {instance}             : Switch default instance',
    'modules                    : Supported games list',
    'create {instance} {module} : Create new instance',
    'shutdown                   : Shutdown system'
  ]
};


exports.system = function($) {
  $.httptool.doGet('/system/info', function(info) {
    let result = '```\n';
    result += 'System : ' + util.humanDuration(info.uptime) + ' UP (v' + info.version + ')\n';
    result += 'CPU    : ' + info.cpu.percent + '%\n';
    result += 'Memory : ' + util.humanFileSize(info.memory.used);
    result += ' / '       + util.humanFileSize(info.memory.total);
    result += ' ('        + info.memory.percent + '%)\n';
    result += 'Disk   : ' + util.humanFileSize(info.disk.used);
    result += ' / '       + util.humanFileSize(info.disk.total);
    result += ' ('        + info.disk.percent + '%)\n';
    result += 'IPv4   : ' + info.net.local + ' ' + info.net.public;
    return result + '\n```';
  });
}

exports.modules = function($) {
  $.httptool.doGet('/modules', function(body) {
    let result = '```\n';
    for (let module in body) {
      result += body[module] + '\n';
    }
    return result + '```';
  });
}

exports.instances = function($) {
  $.message.channel.send($.context.instancesService.getInstancesText());
}

exports.use = function($) {
  if (!util.checkAdmin($.message, $.context.config.ADMIN_ROLE)) return;
  if ($.data.length === 0) return;
  $.context.instancesService.useInstance($.data[0]);
  $.message.channel.send($.context.instancesService.getInstancesText());
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
  let result = '```\nSYSTEM COMMANDS\n' + $.context.config.CMD_PREFIX;
  result += helpText.help.join('\n' + $.context.config.CMD_PREFIX);
  $.message.channel.send(result + '\n```');
}
