import * as cutil from 'common/util/util';
import * as logger from './util/logger.js';

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

export async function newSystemChannels(context) {
  const [self, cache] = [{}, {}];

  self.logChannel = function(channelType, channel, instance = null) {
    const target = instance ? ('instance ' + instance) : 'DEFAULT';
    const channelName = channel ? (channel.name + ' (' + channel.id + ')') : 'UNSET';
    logger.info('Channel ' + channelType + ' for ' + target + ' is ' + channelName);
  };

  self.fetchChannel = async function(channelId) {
    let channel = cutil.hasProp(cache, channelId) ? cache[channelId] : null;
    if (channel) return channel;
    channel = await context.client.channels.fetch(channelId)
      .then(function(result) { return result; })
      .catch(logger.error);
    if (channel) { cache[channelId] = channel; }
    return channel;
  };

  self.fetchChannels = async function(input) {
    const channels = shallowCopyObject(input);
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
      }
    });
    return channels;
  };

  const defaultChannels = await self.fetchChannels(context.config.EVENT_CHANNELS);
  for (const [channelType, channel] of Object.entries(defaultChannels)) { self.logChannel(channelType, channel); }

  self.resolve = function() {
    return shallowCopyObject(defaultChannels);
  };

  return self;
}
