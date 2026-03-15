/* eslint-disable @stylistic/function-paren-newline */
import fetch from 'node-fetch';
import * as cutil from 'common/util/util';
import * as util from '../util/util.js';
import * as logger from '../util/logger.js';
import { startupEvents, serverStates, serverTimedStates,
  playerEvents, playerEventEmojis, emojis } from '../util/literals.js';
import * as subs from '../util/subs.js';
import * as panelhlr from './panelhlr.js';
import * as aliasmehlr from './aliasmehlr.js';
import * as chatbothlr from './chatbothlr.js';
import * as triggerhlr from './triggerhlr.js';

function startPlayerEvents(context, channels, instance, url, aliases,
  panelHandler, triggerHandler, aliasmeHandler, chatbotHandler) {
  if (panelHandler) {
    fetch(url + '/players', util.newGetRequest(context.config.SERVER_TOKEN))
      .then(function(response) {
        if (!response.ok) throw new Error('Status: ' + response.status);
        return response.json();
      })
      .then(function(json) { panelHandler(startupEvents.players, json); })
      .catch(logger.error);
  }
  new subs.Helper(context).daemon(url + '/players/subscribe', function(json) {
    const { event, text } = json;
    if (event === playerEvents.clear) {
      if (triggerHandler) { triggerHandler(event); }
      if (panelHandler) { panelHandler(event); }
      return true;
    }
    const name = json.player && json.player.name ? json.player.name : null;
    if (!name) return true;
    const alias = aliases.findByName(name);
    const displayName = alias ? name + ' `@' + alias.discordid + '`' : name;
    const { login: channelLogin, chat: channelChat } = channels.resolve();
    if (event === playerEvents.chat) {
      if (aliasmeHandler) { aliasmeHandler(text, name); }
      if (chatbotHandler) { chatbotHandler(text); }
      if (channelChat) { channelChat.send('`' + instance + '` ' + emojis.say + ' ' + displayName + ': ' + text); }
      return true;
    }
    if (channelLogin && cutil.hasProp(playerEventEmojis, event)) {  // Events: login, logout, death
      let result = '`' + instance + '` ' + playerEventEmojis[event] + ' ' + displayName;
      if (text) { result += ' [' + text + ']'; }
      if (json.player.steamid) { result += ' [' + json.player.steamid + ']'; }
      channelLogin.send(result);
    }
    const aliasForHandler = alias ? alias : { name: name };
    if (triggerHandler) { triggerHandler(event, aliasForHandler); }
    if (panelHandler) { panelHandler(event, aliasForHandler); }
    return true;
  });
}

function startServerEvents(context, channels, instance, url, panelHandler, triggerHandler) {
  let [state, restartRequired] = [null, false];
  if (panelHandler) {
    fetch(url + '/server', util.newGetRequest(context.config.SERVER_TOKEN))
      .then(function(response) {
        if (!response.ok) throw new Error('Status: ' + response.status);
        return response.json();
      })
      .then(function(json) {
        if (!json || !json.state) return true;  // Ignore
        if (!state) { state = json.state; }
        panelHandler(startupEvents.server, json);
      })
      .catch(logger.error);
  }
  new subs.Helper(context).daemon(url + '/server/subscribe', function(json) {
    if (!json || !json.state) return true;  // Ignore
    if (!state) { state = json.state; }  // Set initial state
    if (json.state === serverStates.start) return true;  // Ignore transient state
    const channelServer = channels.resolve().server;
    if (!restartRequired && json.details.restart) {
      if (channelServer) { channelServer.send('`' + instance + '` ' + emojis.restart + ' restart required'); }
      restartRequired = true;
      return true;
    }
    if (state === json.state) return true;  // Ignore no state change
    state = json.state;
    if (state === serverStates.started) { restartRequired = false; }
    if (channelServer) {
      let text = '`' + instance + '` ' + emojis.satellite + ' ' + state;
      if (serverTimedStates.includes(state) && json.sincelaststate) {
        let seconds = json.sincelaststate / 1000;
        seconds = seconds.toFixed(seconds < 10.0 ? 1 : 0);
        text += ' in ' + seconds + ' seconds';
      } else if (state === serverStates.exception && json.details && json.details.error) {
        text += ' [' + json.details.error + ']';
      }
      channelServer.send(text);
    }
    if (triggerHandler) { triggerHandler(state); }
    if (panelHandler) { panelHandler(state, json); }
    return true;
  });
}

export function startupServerOnly({ context, channels, panels, instance, url, triggers }) {
  const panelHandler = panelhlr.newPanelHandler(context, instance, panels);
  const triggerHandler = triggerhlr.newTriggerHandler(context, channels, instance, triggers);
  startServerEvents(context, channels, instance, url, panelHandler, triggerHandler);
  panelHandler(startupEvents.players, []);  // Init players required
}

export function startupAll({ context, channels, panels, instance, url, triggers, aliases }) {
  const panelHandler = panelhlr.newPanelHandler(context, instance, panels);
  const triggerHandler = triggerhlr.newTriggerHandler(context, channels, instance, triggers);
  const aliasmeHandler = aliasmehlr.newAliasmeHandler(instance, channels, aliases);
  const chatbotHandler = chatbothlr.newChatbotHandler(context, instance, url);
  startServerEvents(context, channels, instance, url, panelHandler, triggerHandler);
  startPlayerEvents(context, channels, instance, url, aliases,
    panelHandler, triggerHandler, aliasmeHandler, chatbotHandler);
}
/* eslint-enable @stylistic/function-paren-newline */
