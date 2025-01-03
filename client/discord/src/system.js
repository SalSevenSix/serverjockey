'use strict';

const util = require('./util.js');
const commons = require('./commons.js');
const helpText = {
  title: 'SYSTEM COMMANDS',
  help1: [
    'help {command} {action}    : Show help',
    'about                      : About ServerJockey',
    'system                     : Show system information',
    'instances                  : Show server instances list',
    'use {instance}             : Switch default instance',
    'modules                    : Supported games list',
    'create {instance} {module} : Create new instance'
  ]
};


exports.help = function($) { commons.sendHelp($, helpText); };

exports.about = function($) {
  let result = '**ServerJockey** is a game server management system for Project Zomboid and other supported games. ';
  result += 'It is designed to be an easy to use self-hosting option for multiplayer servers, ';
  result += 'allowing you to create and remotely manage your servers with a webapp and discord.\n';
  result += '**Join the ServerJockey Discord**\n';
  result += ' https://discord.gg/TEuurWAhHn\n';
  result += '**ServerJockey on Ko-fi**\n';
  result += ' <https://ko-fi.com/D1D4E4ZYZ>\n';
  result += '**ServerJockey on YouTube**\n';
  result += ' <https://www.youtube.com/@BSALIS76>\n';
  result += '**ServerJockey on GitHub**\n';
  result += ' <https://github.com/SalSevenSix/serverjockey>';
  $.message.channel.send(result);
};

exports.system = function($) {
  $.httptool.doGet('/system/info', function(info) {
    let result = '```\n';
    result += 'Version : ' + info.version + '\n';
    result += 'Uptime  : ' + util.humanDuration(info.uptime) + '\n';
    result += 'CPU     : ' + info.cpu.percent + '%\n';
    result += 'Memory  : ' + util.humanFileSize(info.memory.used);
    result += ' / '        + util.humanFileSize(info.memory.total);
    result += ' ('         + info.memory.percent + '%)\n';
    result += 'Disk    : ' + util.humanFileSize(info.disk.used);
    result += ' / '        + util.humanFileSize(info.disk.total);
    result += ' ('         + info.disk.percent + '%)\n';
    result += 'IPv4    : ' + info.net.local + ' ' + info.net.public;
    return result + '\n```';
  });
};

exports.modules = function($) {
  $.httptool.doGet('/modules', function(body) {
    let result = '```\n';
    for (let module in body) {
      result += body[module] + '\n';
    }
    return result + '```';
  });
};

exports.instances = function($) {
  if (!util.checkHasRole($.message, $.context.config.PLAYER_ROLE)) return;
  let result = $.context.instancesService.getInstancesText();
  $.message.channel.send(result);
};

exports.use = function($) {
  if (!util.checkHasRole($.message, $.context.config.ADMIN_ROLE)) return;
  if ($.data.length === 0) return util.reactUnknown($.message);
  if (!$.context.instancesService.useInstance($.data[0])) return util.reactError($.message);
  $.message.channel.send($.context.instancesService.getInstancesText());
};

exports.create = function($) {
  if ($.data.length < 2) return util.reactUnknown($.message);
  const body = { identity: $.data[0], module: $.data[1] };
  $.httptool.doPost('/instances', body, function() {
    $.context.instancesService.setInstance(body.identity);
    util.reactSuccess($.message);
  });
};

exports.shutdown = function($) {
  $.httptool.doPost('/system/shutdown');
};
