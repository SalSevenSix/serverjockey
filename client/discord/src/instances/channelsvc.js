import fs from 'fs';
import * as logger from '../util/logger.js';

/* eslint-disable max-lines-per-function */
export function newInstanceChannels(context, instance) {
  const file = context.config.DATADIR + '/' + instance + '.channel.json';
  const data = { base: [] };
  const self = {};

  const load = async function(input) {
    const [result, channels] = [[], {}];
    input.forEach(function({ channelType, channelId }) {
      channels[channelType] = channelId;
    });
    const fetched = await context.channels.fetchChannels(channels);
    Object.keys(fetched).forEach(function(channelType) {
      const channel = fetched[channelType];
      if (channel) {
        result.push({ channelType: channelType, channelId: channel.id, channel: channel });
        context.channels.logChannel(channelType, channel, instance);
      }
    });
    return result;
  };

  self.load = function() {
    fs.exists(file, function(exists) {
      if (!exists) return;
      fs.readFile(file, function(error, body) {
        if (error) return logger.error(error);
        load(JSON.parse(body)).then(function(result) {
          data.base = result;
        });
      });
    });
    return self;
  };

  self.reset = function(channelType = null) {
    data.base = data.base.filter(function(value) {
      return channelType && channelType != value.channelType;
    });
    return self;
  };

  self.save = function() {
    const payload = data.base.map(function({ channelType, channelId }) {
      return { channelType, channelId };
    });
    fs.writeFile(file, JSON.stringify(payload), logger.error);
  };

  self.set = function(channelType, channel) {
    self.reset(channelType);
    data.base.push({ channelType: channelType, channelId: channel.id, channel: channel });
    return self;
  };

  self.list = function() {
    const result = {};
    for (const [channelType, channelId] of Object.entries(context.channels.config())) {
      result[channelType] = { channelType: channelType, channelId: channelId, isDefault: true };
    }
    data.base.forEach(function({ channelType, channelId }) {
      result[channelType].channelId = channelId;
      result[channelType].isDefault = false;
    });
    return Object.values(result);
  };

  self.resolve = function() {
    const channels = context.channels.resolve();
    data.base.forEach(function({ channelType, channel }) {
      if (channel) { channels[channelType] = channel; }
    });
    return channels;
  };

  return self;
}
/* eslint-enable max-lines-per-function */
