import * as cutil from 'common/util/util';
import * as logger from '../util/logger.js';
import { startupEvents, serverStates, playerEvents } from '../util/literals.js';

function compactArray(value, limit) {
  if (!value) return [];
  const [length, result] = [value.length, [...value]];
  if (length <= limit) return result;
  result.length = limit - 1;
  result.push('(+' + (length - limit + 1) + ' more)');
  return result;
}

function chunkArray(value, rows, columns) {  // TODO move to common
  if (!value) return [];
  if (value.length > rows * columns) {
    rows = Math.ceil(value.length / columns);
  }
  const result = [];
  for (let i = 0; i < columns; i++) {
    result.push(value.slice(i * rows, i * rows + rows));
  }
  return result;
}

function toStatusText({ instance, server, players }) {
  let text = '```\n';
  text += 'Server ' + instance + ' is ';
  if (server.running) {
    text += server.state;
    const details = server.details ? server.details : {};
    if (details.version) { text += '\nVersion : ' + details.version; }
    if (details.ip && details.port) { text += '\nConnect : ' + details.ip + ':' + details.port; }
    text += '\nOnline  : ' + players.length;
    chunkArray(compactArray(players, 36), 3, 12).forEach(function(row) {
      text += '\n';
      row.forEach(function(name, index) {
        name = name.substring(0, 15);
        if (index < 2) { name = name.padEnd(16); }
        text += '| ' + name;
      });
    });
  } else {
    text += 'DOWN';
  }
  text += '\n```';
  text += '\nUpdated <t:' + Math.floor(Date.now() / 1000) + ':R>';
  return text;
}

function newModel(instance) {
  const model = { instance: instance, server: null, players: null };
  const self = {};

  self.resolve = function() {
    if (!model.server || !model.players) return null;
    return { ...model };
  };

  self.updateServer = function(data) {
    model.server = data;
    return true;
  };

  self.playerInit = function(data) {
    model.players = data.map(function({ name }) { return name; });
    return true;
  };

  self.playerLogin = function(data) {
    if (!model.players || model.players.includes(data.name)) return false;
    model.players.push(data.name);
    return true;
  };

  self.playerLogout = function(data) {
    if (!model.players || !model.players.includes(data.name)) return false;
    model.players = model.players.filter(function(name) { return data.name != name; });
    return true;
  };

  self.playerClear = function() {
    if (!model.players || model.players.length === 0) return false;
    model.players = [];
    return true;
  };

  return self;
}

/* eslint-disable max-lines-per-function */
function newUpdater(context, panels, resolve) {
  const data = { panels: [] };

  const remove = function(panel, reason) {
    panel.synced = true;  // To ignore if re-queued
    data.panels = data.panels.filter(function(value) { return !(panel.entry === value.entry); });
    panels.remove(panel.entry.channelId, panel.entry.messageId).save();
    logger.info('Panel Updater ' + reason);
    return false;
  };

  const renderer = function(panel) {
    return async function() {
      if (panel.synced) return false;  // Ignore
      if (!panel.message) {  // Lazy load message
        const channel = await context.channels.fetch(panel.entry.channelId).catch(logger.error);
        if (!channel) return remove(panel, 'failed to fetch channel: ' + panel.entry.channelId);
        panel.message = await channel.messages.fetch(panel.entry.messageId).catch(logger.error);
        if (!panel.message) return remove(panel, 'failed to fetch message: ' + panel.entry.messageId);
      }
      const model = resolve();
      if (!model) {  // Model not initialised yet
        context.cooldowns.submit(renderer(panel));
        return false;
      }
      panel.synced = true;
      const result = await panel.message.edit(toStatusText(model)).catch(logger.error);
      if (!result) return remove(panel, 'failed to edit message: ' + panel.entry.messageId);
      return true;
    };
  };

  const update = function() {
    data.panels.forEach(function(panel) {
      if (!panel.synced) return;  // Already on queue
      panel.synced = false;
      context.cooldowns.submit(renderer(panel));
    });
  };

  panels.onLoad(function() {
    data.panels = panels.list().map(function(entry) { return { entry: entry, message: null, synced: true }; });
    update();
  });

  panels.onAdd(function(entry, message) {
    cutil.sleep(1000).then(function() {
      const panel = { entry: entry, message: message, synced: false };
      data.panels.push(panel);
      context.cooldowns.submit(renderer(panel));
    });
  });

  return update;
}
/* eslint-enable max-lines-per-function */

export function newPanelHandler(context, instance, panels) {
  const model = newModel(instance);
  const updater = newUpdater(context, panels, model.resolve);
  const handlers = {
    [startupEvents.server]: model.updateServer,
    [serverStates.ready]: model.updateServer,
    [serverStates.maintenance]: model.updateServer,
    [serverStates.started]: model.updateServer,
    [serverStates.stopped]: model.updateServer,
    [serverStates.exception]: model.updateServer,
    [startupEvents.players]: model.playerInit,
    [playerEvents.login]: model.playerLogin,
    [playerEvents.logout]: model.playerLogout,
    [playerEvents.clear]: model.playerClear
  };
  return function(event, data = null) {
    if (!cutil.hasProp(handlers, event)) return;
    if (handlers[event](data)) { updater(); }
  };
}
