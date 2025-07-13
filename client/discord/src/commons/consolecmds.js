import * as cutil from 'common/util/util';
import * as msgutil from '../util/msgutil.js';

export function send({ httptool, message, data }) {
  if (data.length === 0) return msgutil.reactUnknown(message);
  const line = msgutil.extractCommandLine(message);
  httptool.doPost('/console/send', { line: line }, function(text) {
    if (!text) return msgutil.reactSuccess(message);
    msgutil.sendText(message, text);
  });
}

export function say({ context, httptool, message, data }) {
  if (data.length === 0) return msgutil.reactUnknown(message);
  const name = msgutil.extractUserTag(message);
  const line = msgutil.extractCommandLine(message);
  httptool.doPost(
    '/console/say', { player: name, text: line },
    function() { message.react('💬'); },
    context.config.PLAYER_ROLE
  );
}

export function players({ httptool, aliases, instance }) {
  httptool.doGet('/players', function(body) {
    const result = [instance + ' players online: ' + body.length];
    if (body.length === 0) return result;
    const plen = Math.max(10, 2 + body.reduce(function(a, b) {
      return a.name.length > b.name.length ? a : b;
    }).name.length);
    body.forEach(function(entry) {
      let line = entry.name.padEnd(plen);
      if (entry.steamid) { line = entry.steamid + ' ' + line; }
      else if (entry.steamid === '') { line = 'CONNECTED         ' + line; }
      if (cutil.hasProp(entry, 'uptime')) { line += cutil.humanDuration(entry.uptime, 'hm').padEnd(8); }
      else { line += '        '; }
      const playerAlias = aliases.findByName(entry.name);
      if (playerAlias) { line += ' @' + playerAlias.discordid; }
      result.push(line.trim());
    });
    return result;
  });
}
