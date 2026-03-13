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

export function panel({ context, panels, message, data }) {
  const cmd = data.length > 0 ? data[0] : 'list';
  if (cmd === 'list') {
    msgutil.sendText(message, JSON.stringify(panels.list()));  // TODO proper formatting
  } else if (cmd === 'status-text') {
    message.channel.send(placeholderText().join('\n'))
      .then(function(result) {
        context.channels.remember(result.channel);
        panels.add(cmd, result).save();
      })
      .catch(function(error) { logger.error(error, message); });
  } else {
    msgutil.reactUnknown(message);
  }
}
