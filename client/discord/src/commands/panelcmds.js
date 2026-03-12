import * as logger from '../util/logger.js';
import * as msgutil from '../util/msgutil.js';

function toStatusText({ instance, status, players }) {
  const details = status.details;
  const [online, names] = [players.length, players.map(function(player) { return player.name; })];
  let text = '```\n';
  text += 'Server ' + instance + ' is ';
  if (status.running) {
    text += status.state;
    if (details.version) { text += '\nVersion: ' + details.version; }
    if (details.ip && details.port) { text += '\nConnect: ' + details.ip + ':' + details.port; }
    text += '\nOnline : ' + online;
    if (online > 0) { text += '\n- ' + names.join('\n- '); }
  } else {
    text += 'DOWN';
  }
  text += '\n```';
  return text;
}

export function panel({ context, httptool, instance, panels, message, data }) {
  const cmd = data.length > 0 ? data[0] : 'list';
  if (cmd === 'list') {
    msgutil.sendText(message, JSON.stringify(panels.list()));
  } else if (cmd === 'status-text') {
    httptool.doGet('/server', function(status) {
      httptool.doGet('/players', function(players) {
        message.channel.send(toStatusText({ instance, status, players }))
          .then(function(result) {
            context.channels.remember(result.channel);
            panels.add(cmd, result).save();
          })
          .catch(function(error) { logger.error(error, message); });
      });
    });
  } else {
    msgutil.reactUnknown(message);
  }
}
