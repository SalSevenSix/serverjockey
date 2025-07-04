import * as cutil from 'common/util/util';
import * as msgutil from './util/msgutil.js';
import * as helptext from './helptext.js';

export const help = helptext.systemHelp;

export function about({ message }) {
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
  message.channel.send(result);
}

export function system({ httptool }) {
  httptool.doGet('/system/info', function(info) {
    let result = 'Version : ' + info.version + '\n';
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
    return [result];
  });
}

export function modules({ httptool }) {
  httptool.doGet('/modules', function(body) {
    return Object.keys(body);
  });
}

export function instances({ context, message }) {
  if (!msgutil.checkHasRole(message, context.config.PLAYER_ROLE)) return;
  msgutil.sendText(message, context.instancesService.getInstancesText());
}

export function use({ context, message, data }) {
  if (!msgutil.checkHasRole(message, context.config.ADMIN_ROLE)) return;
  let text = context.instancesService.currentInstance();
  if (data.length === 0) {
    if (text) { text = 'default => ' + text; }
    else { text = 'No default instance'; }
  } else {
    if (!context.instancesService.useInstance(data[0])) return msgutil.reactError(message);
    text = context.instancesService.getInstancesText();
  }
  msgutil.sendText(message, text);
}

export function create({ context, httptool, message, data }) {
  if (data.length < 2) return msgutil.reactUnknown(message);
  const body = { identity: data[0], module: data[1] };
  httptool.doPost('/instances', body, function() {
    context.instancesService.useInstance(body.identity, true);
    msgutil.reactSuccess(message);
  });
}

export function shutdown({ httptool }) {
  httptool.doPost('/system/shutdown');
}
