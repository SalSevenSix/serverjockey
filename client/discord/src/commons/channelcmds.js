import * as util from '../util/util.js';
import * as msgutil from '../util/msgutil.js';

export function channel({ context, channels, instance, message, data }) {
  const cmd = data.length > 0 ? data[0] : 'list';
  if (cmd === 'list') {
    const channelsList = channels.list();
    let text = ['No Instance Channels'];
    if (channelsList.length > 0) {
      text = channelsList.map(function({ channelType, channelId }) {
        if (channelType === 'login') { channelType = 'player'; }
        return '`' + channelType.padEnd(6) + ' =>` <#' + channelId + '>';
      });
    }
    msgutil.sendText(message, text, false);
  } else if (['server', 'player', 'chat'].includes(cmd)) {
    if (data.length < 2) return msgutil.reactUnknown(message);
    const [channelType, action] = [cmd === 'player' ? 'login' : cmd, data[1]];
    if (action === 'reset') {
      channels.reset(channelType).save();
      context.channels.logChannel(channelType, null, instance);
      msgutil.reactSuccess(message);
    } else {  // Action is channel
      const channelId = util.toSnowflake(action, '<#');
      if (!channelId) return msgutil.reactError(message);
      context.channels.fetchChannel(channelId).then(function(result) {
        if (!result) return msgutil.reactError(message);
        channels.set(channelType, result).save();
        context.channels.logChannel(channelType, result, instance);
        msgutil.reactSuccess(message);
      });
    }
  } else {
    msgutil.reactUnknown(message);
  }
}
