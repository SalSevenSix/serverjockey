import * as cutil from 'common/util/util';
import * as literals from '../util/literals.js';
import * as logger from '../util/logger.js';
import * as msgutil from '../util/msgutil.js';
import * as subs from '../util/subs.js';

export function status({ httptool, instance }) {
  httptool.doGet('/server', function(body) {
    let result = 'Server ' + instance + ' is ';
    if (!body.running) return [result + 'DOWN'];
    result += body.state;
    if (body.uptime) { result += ' (' + cutil.humanDuration(body.uptime) + ')'; }
    const dtl = body.details ? body.details : {};
    if (dtl.version) { result += '\nVersion:  ' + dtl.version; }
    if (dtl.ip && dtl.port) { result += '\nConnect:  ' + dtl.ip + ':' + dtl.port; }
    if (dtl.auth) { result += '\nAuth:     ' + (cutil.isString(dtl.auth) ? dtl.auth : '[see webapp]'); }
    if (dtl.ingametime) { result += '\nIngame:   ' + dtl.ingametime; }
    if (dtl.map) { result += '\nMap:      ' + dtl.map; }
    if (dtl.notice) { result += '\nNotice:   ' + dtl.notice; }
    if (dtl.restart) { result += '\nSERVER RESTART REQUIRED'; }
    return [result];
  });
}

export function server({ context, httptool, instance, message, data }) {
  if (data.length === 0) return status({ httptool, instance });
  const { serverSignals: sg, serverStates: ss, serverUpStates: upStates, serverDownStates: downStates } = literals;
  let cmd = data[0].toLowerCase();
  if (cmd === sg.restart) { cmd = sg.restartImmediately; }
  if (!Object.values(sg).includes(cmd)) return msgutil.reactUnknown(message);
  httptool.doPost('/server/' + cmd, { respond: true }, function(json) {
    let [state, target] = [json.current.state, cmd === sg.start];
    if ((target ? upStates : downStates).includes(state)) return msgutil.reactError(message);
    if ([sg.restartWarnings, sg.restartEmpty].includes(cmd)) return msgutil.reactSuccess(message);
    msgutil.reactWait(message);
    target ||= cmd === sg.restartImmediately;
    new subs.Helper(context).poll(json.url, function(polldata) {
      if (state === polldata.state) return true;
      state = polldata.state;
      if (state === ss.exception) return msgutil.rmReacts(message, msgutil.reactError, logger.error, false);
      if (target && state === ss.started) return msgutil.rmReacts(message, msgutil.reactSuccess, logger.error, false);
      if (!target && state === ss.stopped) return msgutil.rmReacts(message, msgutil.reactSuccess, logger.error, false);
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
