import { emojis } from '../util/literals.js';
import * as subs from '../util/subs.js';
import * as aliasmehlr from './aliasmehlr.js';
import * as chatbothlr from './chatbothlr.js';
import * as triggerhlr from './triggerhlr.js';

function startPlayerEvents(context, channels, instance, url, aliases, triggerHandler, aliasmeHandler, chatbotHandler) {
  new subs.Helper(context).daemon(url + '/players/subscribe', function(json) {
    const [event, text] = [json.event, json.text];
    if (event === 'CLEAR') {
      if (triggerHandler) { triggerHandler(event); }
      return true;
    }
    const name = json.player && json.player.name ? json.player.name : null;
    if (!name) return true;
    const alias = aliases.findByName(name);
    const displayName = alias ? name + ' `@' + alias.discordid + '`' : name;
    const { login: channelLogin, chat: channelChat } = channels.resolve();
    if (event === 'CHAT') {
      if (aliasmeHandler) { aliasmeHandler(text, name); }
      if (chatbotHandler) { chatbotHandler(text); }
      if (channelChat) { channelChat.send('`' + instance + '` ' + emojis.say + ' ' + displayName + ': ' + text); }
      return true;
    }
    if (channelLogin) {
      let result = null;
      if (event === 'LOGIN') { result = emojis.greendot; }
      else if (event === 'LOGOUT') { result = emojis.reddot; }
      else if (event === 'DEATH') { result = emojis.skull; }
      if (!result) return true;
      result = '`' + instance + '` ' + result + ' ' + displayName;
      if (text) { result += ' [' + text + ']'; }
      if (json.player.steamid) { result += ' [' + json.player.steamid + ']'; }
      channelLogin.send(result);
    }
    if (triggerHandler) { triggerHandler(event, alias ? alias : { name: name }); }
    return true;
  });
}

function startServerEvents(context, channels, instance, url, triggerHandler) {
  let [state, restartRequired] = [null, false];
  new subs.Helper(context).daemon(url + '/server/subscribe', function(json) {
    if (!json.state) return true;  // Ignore no state
    if (!state) { state = json.state; }  // Set initial state
    if (json.state === 'START') return true;  // Ignore transient state
    const channelServer = channels.resolve().server;
    if (!restartRequired && json.details.restart) {
      if (channelServer) { channelServer.send('`' + instance + '` ' + emojis.restart + ' restart required'); }
      restartRequired = true;
      return true;
    }
    if (state === json.state) return true;  // Ignore no state change
    state = json.state;
    if (state === 'STARTED') { restartRequired = false; }
    if (channelServer) {
      let text = '`' + instance + '` ' + emojis.satellite + ' ' + state;
      if (['READY', 'STARTED', 'STOPPED'].includes(state) && json.sincelaststate) {
        let seconds = json.sincelaststate / 1000;
        seconds = seconds.toFixed(seconds < 10.0 ? 1 : 0);
        text += ' in ' + seconds + ' seconds';
      } else if (state === 'EXCEPTION' && json.details && json.details.error) {
        text += ' [' + json.details.error + ']';
      }
      channelServer.send(text);
    }
    if (triggerHandler) { triggerHandler(state); }
    return true;
  });
}

export function startupServerOnly({ context, channels, instance, url, triggers }) {
  const triggerHandler = triggerhlr.newTriggerHandler(context, channels, instance, triggers);
  startServerEvents(context, channels, instance, url, triggerHandler);
}

export function startupAll({ context, channels, instance, url, triggers, aliases }) {
  const triggerHandler = triggerhlr.newTriggerHandler(context, channels, instance, triggers);
  const aliasmeHandler = aliasmehlr.newAliasmeHandler(instance, channels, aliases);
  const chatbotHandler = chatbothlr.newChatbotHandler(context, instance, url);
  startServerEvents(context, channels, instance, url, triggerHandler);
  startPlayerEvents(context, channels, instance, url, aliases, triggerHandler, aliasmeHandler, chatbotHandler);
}
