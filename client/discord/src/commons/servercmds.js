import fs from 'fs';
import * as cutil from 'common/util/util';
import * as util from '../util/util.js';
import * as logger from '../util/logger.js';
import * as subs from '../util/subs.js';

export function server({ context, httptool, instance, message, data }) {
  if (data.length === 0) {
    return httptool.doGet('/server', function(body) {
      let result = '```\nServer ' + instance + ' is ';
      if (!body.running) return result + 'DOWN\n```';
      result += body.state;
      if (body.uptime) { result += ' (' + cutil.humanDuration(body.uptime) + ')'; }
      result += '\n';
      const dtl = body.details;
      if (dtl.version) { result += 'Version:  ' + dtl.version + '\n'; }
      if (dtl.ip && dtl.port) { result += 'Connect:  ' + dtl.ip + ':' + dtl.port + '\n'; }
      if (dtl.ingametime) { result += 'Ingame:   ' + dtl.ingametime + '\n'; }
      if (dtl.map) { result += 'Map:      ' + dtl.map + '\n'; }
      if (dtl.restart) { result += 'SERVER RESTART REQUIRED\n'; }
      return result + '```';
    });
  }
  const signals = ['start', 'restart-immediately', 'restart-after-warnings', 'restart-on-empty', 'stop'];
  const upStates = ['START', 'STARTING', 'STARTED', 'STOPPING'];
  const downStates = ['READY', 'STOPPED', 'EXCEPTION'];
  let cmd = data[0].toLowerCase();
  if (cmd === 'restart') { cmd = signals[1]; }
  if (!signals.includes(cmd)) return util.reactUnknown(message);
  httptool.doPost('/server/' + cmd, { respond: true }, function(json) {
    let state = json.current.state;
    let targetUp = cmd === signals[0];
    if (targetUp && upStates.includes(state)) return util.reactError(message);
    if (!targetUp && downStates.includes(state)) return util.reactError(message);
    if ([signals[2], signals[3]].includes(cmd)) return util.reactSuccess(message);
    util.reactWait(message);
    targetUp ||= cmd === signals[1];
    new subs.Helper(context).poll(json.url, function(polldata) {
      if (state === polldata.state) return true;
      state = polldata.state;
      if (state === downStates[2]) return util.rmReacts(message, util.reactError, logger.error, false);
      if (targetUp && state === upStates[2]) return util.rmReacts(message, util.reactSuccess, logger.error, false);
      if (!targetUp && state === downStates[1]) return util.rmReacts(message, util.reactSuccess, logger.error, false);
      return true;
    });
  });
}

export function auto({ httptool, instance, data }) {
  if (data.length > 0) return httptool.doPost('', { auto: data[0] });
  const desc = ['Off', 'Auto Start', 'Auto Restart', 'Auto Start and Restart'];
  httptool.doGet('/server', function(body) {
    let result = '```\n' + instance;
    result += ' auto mode: ' + body.auto;
    result += ' (' + desc[body.auto] + ')\n```';
    return result;
  });
}

export function log({ httptool, message }) {
  httptool.doGet('/log/tail', function(body) {
    if (!body) return message.channel.send('```\nNo log lines found\n```');
    const fname = 'log-' + message.id + '.text';
    const fpath = '/tmp/' + fname;
    fs.writeFile(fpath, body, function(error) {
      if (error) return logger.error(error);
      message.channel.send({ files: [{ attachment: fpath, name: fname }] })
        .finally(function() { fs.unlink(fpath, logger.error); });
    });
  });
}
