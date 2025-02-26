import * as subs from '../subs.js';

function startServerEvents($) {
  const [context, channels, instance, url] = [$.context, $.channels, $.instance, $.url];
  if (!channels.server) return;
  let state = 'READY';
  let restartRequired = false;
  new subs.Helper(context).daemon(url + '/server/subscribe', function(json) {
    if (!json.state) return true;  // Ignore no state
    if (json.state === 'START') return true;  // Ignore transient state
    if (!restartRequired && json.details.restart) {
      channels.server.send('`' + instance + '` 🔄 restart required');
      restartRequired = true;
      return true;
    }
    if (state === json.state) return true;  // Ignore no state change
    state = json.state;
    if (state === 'STARTED') { restartRequired = false; }
    channels.server.send('`' + instance + '` 📡 ' + state);
    return true;
  });
}

function startPlayerEvents($) {
  const [context, channels, aliases, instance, url] = [$.context, $.channels, $.aliases, $.instance, $.url];
  if (!channels.login && !channels.chat) return;
  new subs.Helper(context).daemon(url + '/players/subscribe', function(json) {
    let playerName = json.player && json.player.name ? json.player.name : null;
    if (!playerName) return true;
    const playerAlias = aliases.findByName(playerName);
    if (playerAlias) { playerName += ' `@' + playerAlias.discordid + '`'; }
    if (json.event === 'CHAT') {
      if (!channels.chat) return true;
      channels.chat.send('`' + instance + '` 💬 ' + playerName + ': ' + json.text);
      return true;
    }
    if (!channels.login) return true;
    let result = null;
    if (json.event === 'LOGIN') { result = ' 🟢 '; }
    else if (json.event === 'LOGOUT') { result = ' 🔴 '; }
    else if (json.event === 'DEATH') { result = ' 💀 '; }
    if (!result) return true;
    result = '`' + instance + '`' + result + playerName;
    if (json.text) { result += ' [' + json.text + ']'; }
    if (json.player.steamid) { result += ' [' + json.player.steamid + ']'; }
    channels.login.send(result);
    return true;
  });
}

export function startupServerOnly($) {
  startServerEvents($);
}

export function startupAll($) {
  startServerEvents($);
  startPlayerEvents($);
}
