const { messageLink } = require('discord.js');
import * as logger from '../util/logger.js';
import * as msgutil from '../util/msgutil.js';

function placeholderText() {
  return [
    '```',
    '##############################',
    '#                            #',
    '#    SERVER STATUS PANEL     #',
    '#    waiting for update!     #',
    '#                            #',
    '##############################',
    '```'
  ];
}

export function panel({ panels, message, data }) {
  const cmd = data.length > 0 ? data[0] : 'list';
  if (cmd === 'list') {
    const panelsList = panels.list();
    if (panelsList.length === 0) return msgutil.sendText(message, ['No Instance Panels']);
    const result = panelsList.map(function({ panelType, channelId, messageId }, index) {
      let text = '`' + index + ' | ' + panelType.padEnd(12) + ' =>` ';
      text += messageLink(channelId, messageId, message.guild.id);
      return text;
    });
    msgutil.sendText(message, result, false);
  } else if (cmd === 'status-text') {
    message.channel.send(placeholderText().join('\n'))
      .then(function(result) { panels.add(cmd, result).save(); })
      .catch(function(error) { logger.error(error, message); });
  } else {
    msgutil.reactUnknown(message);
  }
}
