import * as cutil from 'common/util/util';
import * as logger from '../util/logger.js';

function shallowCopyObject(input) {
  const result = {};
  for (const [key, value] of Object.entries(input)) {
    result[key] = value ? value : null;
  }
  return result;
}

function toChannelMap(channels) {
  const result = {};
  channels.forEach(function(channel) {
    if (channel) { result[channel.id] = channel; }
  });
  return result;
}

function newInstanceChannels(systemChannels, instance) {
  const self = {};

  self.load = function() { return self; };

  self.reset = function() { return self; };

  self.save = function() { logger.info('Saved ' + instance); };

  self.resolve = function() {
    return systemChannels.resolve();
  };

  return self;
}

export async function newSystemChannels(context) {
  const [self, cache] = [{}, {}];

  self.fetchChannel = async function(channelId) {
    let channel = cutil.hasProp(cache, channelId) ? cache[channelId] : null;
    if (channel) return channel;
    channel = await context.client.channels.fetch(channelId)
      .then(function(result) { return result; })
      .catch(logger.error);
    if (channel) { cache[channelId] = channel; }
    return channel;
  };

  self.fetchChannels = async function(channels) {
    let results = [...new Set(Object.values(channels))];
    results = results.filter(function(channelId) { return channelId; });
    if (results.length === 0) return channels;
    results = results.map(function(channelId) { return self.fetchChannel(channelId); });
    results = await Promise.all(results);
    results = toChannelMap(results);
    Object.keys(channels).forEach(function(channelType) {
      const channelId = channels[channelType];
      channels[channelType] = null;
      if (channelId && cutil.hasProp(results, channelId)) {
        channels[channelType] = results[channelId];
        logger.info('Publishing ' + channelType + ' events to ' + channels[channelType].name + ' (' + channelId + ')');
      }
    });
    return channels;
  };

  const defaultChannels = await self.fetchChannels(shallowCopyObject(context.config.EVENT_CHANNELS));

  self.resolve = function() {
    return shallowCopyObject(defaultChannels);
  };

  self.newInstanceChannels = function(instance) {
    return newInstanceChannels(self, instance);
  };

  return self;
}
