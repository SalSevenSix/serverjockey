const cutil = require('common/util/util');
const util = require('./util.js');
const helptext = require('./helptext.js');

export const help = helptext.help(helptext.systemHelpData);

export function about($) {
  let result = '**ServerJockey** is a game server management system for Project Zomboid and other supported games. ';
  result += 'It is designed to be an easy to use self-hosting option for multiplayer servers, ';
  result += 'allowing you to create and remotely manage your servers with a webapp and discord.\n';
  result += '**Join the ServerJockey Discord**\n';
  result += ' https://discord.gg/TEuurWAhHn\n';
  result += '**ServerJockey on Ko-fi**\n';
  result += ' <https://ko-fi.com/serverjockey>\n';
  result += '**ServerJockey on YouTube**\n';
  result += ' <https://www.youtube.com/@BSALIS76>\n';
  result += '**ServerJockey on GitHub**\n';
  result += ' <https://github.com/SalSevenSix/serverjockey>';
  $.message.channel.send(result);
}

export function system($) {
  $.httptool.doGet('/system/info', function(info) {
    let result = '```\n';
    result += 'Version : ' + info.version + '\n';
    result += 'Svrtime : ' + info.time.text + ' ' + info.time.tz.text + '\n';
    result += 'Uptime  : ' + cutil.humanDuration(info.uptime) + '\n';
    result += 'CPU     : ' + info.cpu.percent + '%\n';
    result += 'Memory  : ' + cutil.humanFileSize(info.memory.used);
    result += ' / ' + cutil.humanFileSize(info.memory.total);
    result += ' (' + info.memory.percent + '%)\n';
    result += 'Disk    : ' + cutil.humanFileSize(info.disk.used);
    result += ' / ' + cutil.humanFileSize(info.disk.total);
    result += ' (' + info.disk.percent + '%)\n';
    result += 'IPv4    : ' + info.net.local + ' ' + info.net.public;
    result += '\n```';
    return result;
  });
}

export function modules($) {
  $.httptool.doGet('/modules', function(body) {
    return '```\n' + body.join('\n') + '\n```';
  });
}

export function instances($) {
  if (!util.checkHasRole($.message, $.context.config.PLAYER_ROLE)) return;
  $.message.channel.send($.context.instancesService.getInstancesText());
}

export function use($) {
  if (!util.checkHasRole($.message, $.context.config.ADMIN_ROLE)) return;
  if ($.data.length === 0) {
    if ($.context.instancesService.currentInstance()) {
      $.message.channel.send('```\ndefault => ' + $.context.instancesService.currentInstance() + '\n```');
    } else {
      $.message.channel.send('```\nNo default instance set\n```');
    }
  } else {
    if (!$.context.instancesService.useInstance($.data[0])) return util.reactError($.message);
    $.message.channel.send($.context.instancesService.getInstancesText());
  }
}

export function create($) {
  if ($.data.length < 2) return util.reactUnknown($.message);
  const body = { identity: $.data[0], module: $.data[1] };
  $.httptool.doPost('/instances', body, function() {
    $.context.instancesService.setInstance(body.identity);
    util.reactSuccess($.message);
  });
}

export function shutdown($) {
  $.httptool.doPost('/system/shutdown');
}
