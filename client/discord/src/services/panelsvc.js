import fs from 'fs';
import * as logger from '../util/logger.js';

/* eslint-disable max-lines-per-function */
export function newPanels(context, instance) {
  const file = context.config.DATADIR + '/' + instance + '.panel.json';
  const data = { base: [], loaded: false };
  const callbacks = { onLoad: null, onAdd: null };
  const self = {};

  data.set = function(value = null) {
    if (value) { data.base = value; }
    data.loaded = true;
    if (callbacks.onLoad) { callbacks.onLoad(); }
  };

  self.onLoad = function(callback) {
    callbacks.onLoad = callback;
    if (data.loaded) { callback(); }
  };

  self.load = function() {
    fs.exists(file, function(exists) {
      if (!exists) return data.set();
      fs.readFile(file, function(error, body) {
        data.set(error ? null : JSON.parse(body));
        if (error) { logger.error(error); }
      });
    });
    return self;
  };

  self.reset = function() {
    data.base = [];
    return self;
  };

  self.save = function() {
    fs.writeFile(file, JSON.stringify(data.base), logger.error);
  };

  self.remove = function(channelId, messageId) {
    data.base = data.base.filter(function(value) {
      return !(value.channelId === channelId && value.messageId === messageId);
    });
    return self;
  };

  self.onAdd = function(callback) {
    callbacks.onAdd = callback;
  };

  self.add = function(panelType, message, thumbUrl = null) {
    const [channelId, messageId] = [message.channel.id, message.id];
    self.remove(channelId, messageId);
    const entry = { panelType, channelId, messageId };
    if (thumbUrl) { entry.thumbUrl = thumbUrl; }
    data.base.push(entry);
    if (callbacks.onAdd) { callbacks.onAdd(entry, message); }
    return self;
  };

  self.list = function() {
    return data.base.map(function({ panelType, channelId, messageId, thumbUrl }) {
      const entry = { panelType, channelId, messageId };
      if (thumbUrl) { entry.thumbUrl = thumbUrl; }
      return entry;
    });
  };

  return self;
}
/* eslint-enable max-lines-per-function */
