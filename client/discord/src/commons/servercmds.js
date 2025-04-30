import * as cutil from 'common/util/util';
import * as logger from '../util/logger.js';
import * as msgutil from '../util/msgutil.js';
import * as subs from '../util/subs.js';

export function server({ context, httptool, instance, message, data }) {
  if (data.length === 0) {
    return httptool.doGet('/server', function(body) {
      let result = 'Server ' + instance + ' is ';
      if (!body.running) return [result + 'DOWN'];
      result += body.state;
      if (body.uptime) { result += ' (' + cutil.humanDuration(body.uptime) + ')'; }
      result += '\n';
      const dtl = body.details;
      if (dtl.version) { result += 'Version:  ' + dtl.version + '\n'; }
      if (dtl.ip && dtl.port) { result += 'Connect:  ' + dtl.ip + ':' + dtl.port + '\n'; }
      if (dtl.ingametime) { result += 'Ingame:   ' + dtl.ingametime + '\n'; }
      if (dtl.map) { result += 'Map:      ' + dtl.map + '\n'; }
      if (dtl.restart) { result += 'SERVER RESTART REQUIRED\n'; }
      return [result.trim()];
    });
  }
  const signals = ['start', 'restart-immediately', 'restart-after-warnings', 'restart-on-empty', 'stop'];
  const upStates = ['START', 'STARTING', 'STARTED', 'STOPPING'];
  const downStates = ['READY', 'STOPPED', 'EXCEPTION'];
  let cmd = data[0].toLowerCase();
  if (cmd === 'restart') { cmd = signals[1]; }
  if (!signals.includes(cmd)) return msgutil.reactUnknown(message);
  httptool.doPost('/server/' + cmd, { respond: true }, function(json) {
    let state = json.current.state;
    let tgt = cmd === signals[0];
    if (tgt && upStates.includes(state)) return msgutil.reactError(message);
    if (!tgt && downStates.includes(state)) return msgutil.reactError(message);
    if ([signals[2], signals[3]].includes(cmd)) return msgutil.reactSuccess(message);
    msgutil.reactWait(message);
    tgt ||= cmd === signals[1];
    new subs.Helper(context).poll(json.url, function(polldata) {
      if (state === polldata.state) return true;
      state = polldata.state;
      if (state === downStates[2]) return msgutil.rmReacts(message, msgutil.reactError, logger.error, false);
      if (tgt && state === upStates[2]) return msgutil.rmReacts(message, msgutil.reactSuccess, logger.error, false);
      if (!tgt && state === downStates[1]) return msgutil.rmReacts(message, msgutil.reactSuccess, logger.error, false);
      return true;
    });
  });
}

export function auto({ httptool, instance, data }) {
  if (data.length > 0) return httptool.doPost('', { auto: data[0] });
  const desc = ['Off', 'Auto Start', 'Auto Restart', 'Auto Start and Restart'];
  httptool.doGet('/server', function(body) {
    return [instance + ' auto mode: ' + body.auto + ' (' + desc[body.auto] + ')'];
  });
}

export function log({ httptool, message }) {
  httptool.doGet('/log/tail', function(body) {
    if (!body) return ['No log lines found'];
    return msgutil.sendFile(message, body, 'log');
  });
}
