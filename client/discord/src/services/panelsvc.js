import fs from 'fs';
import * as logger from '../util/logger.js';

export function newPanels(context, instance) {
  const file = context.config.DATADIR + '/' + instance + '.panel.json';
  const data = { base: [] };
  const self = {};

  self.load = function() {
    fs.exists(file, function(exists) {
      if (!exists) return;
      fs.readFile(file, function(error, body) {
        if (error) return logger.error(error);
        data.base = JSON.parse(body);
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

  self.remove = function(message) {
    data.base = data.base.filter(function({ channelId, messageId }) {
      return !(channelId === message.channel.id && messageId === message.id);
    });
    return self;
  };

  self.add = function(panelType, message) {
    self.remove(message);
    data.base.push({ panelType: panelType, channelId: message.channel.id, messageId: message.id });
    return self;
  };

  self.list = function() {
    return data.base.map(function({ panelType, channelId, messageId }) {
      return { panelType, channelId, messageId };
    });
  };

  return self;
}
