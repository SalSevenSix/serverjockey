import * as cutil from 'common/util/util';
import * as logger from '../util/logger.js';

export async function fetchDefaultChannels(context) {
  const channelConfig = context.config.EVENT_CHANNELS;
  const channels = { server: null, login: null, chat: null };
  Object.keys(channels).forEach(function(channelType) {
    if (cutil.hasProp(channelConfig, channelType) && channelConfig[channelType]) {
      channels[channelType] = channelConfig[channelType];
    }
  });
  let promises = [...new Set(Object.values(channels))];
  promises = promises.filter(function(channelId) { return channelId; });
  promises = promises.map(function(channelId) {
    return context.client.channels.fetch(channelId).then(function(channel) { return channel; }).catch(logger.error);
  });
  const results = await Promise.all(promises);
  const channelMap = {};
  results.forEach(function(channel) {
    if (channel) { channelMap[channel.id] = channel; }
  });
  Object.keys(channels).forEach(function(channelType) {
    const channelId = channels[channelType];
    channels[channelType] = null;
    if (channelId && cutil.hasProp(channelMap, channelId)) {
      channels[channelType] = channelMap[channelId];
      logger.info('Publishing ' + channelType + ' events to ' + channels[channelType].name + ' (' + channelId + ')');
    }
  });
  return channels;
}
