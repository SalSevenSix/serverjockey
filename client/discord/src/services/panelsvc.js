import * as io from '../util/io.js';

/* eslint-disable max-lines-per-function */
export function newPanels(context, instance) {
  const file = context.config.DATADIR + '/' + instance + '.panel.json';
  const data = { base: [], loaded: false };
  const callbacks = { onLoad: null, onAdd: null };
  const self = {};

  data.set = function(body = null) {
    if (body) { data.base = JSON.parse(body); }
    data.loaded = true;
    if (callbacks.onLoad) { callbacks.onLoad(); }
  };

  self.onLoad = function(callback) {
    callbacks.onLoad = callback;
    if (data.loaded) { callback(); }
  };

  self.load = function() {
    io.fileRead(file, data.set, data.set, data.set);
    return self;
  };

  self.reset = function() {
    data.base = [];
    return self;
  };

  self.save = function() {
    io.fileSaveArray(file, data.base);
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
