const { messageLink, EmbedBuilder } = require('discord.js');
import { emojis, assetUrls, colourCodes } from '../util/literals.js';
import * as logger from '../util/logger.js';
import * as msgutil from '../util/msgutil.js';

function placeholderText() {
  return [
    '```',
    '#####################################################',
    '#                                                   #',
    '#                 SERVER STATUS PANEL               #',
    '#                 waiting for update!               #',
    '#                                                   #',
    '#####################################################',
    '```'
  ];
}

function placeholderEmbed(thumbUrl) {
  if (!thumbUrl) { thumbUrl = assetUrls.sjgmsIconMedium; }
  return new EmbedBuilder().setColor(colourCodes.light).setTitle('Server Status Panel')
    .setDescription(emojis.wait + ' waiting for update!').setThumbnail(thumbUrl).setTimestamp();
}

function extractArgs(data) {
  let [notes, thumbUrl] = [null, null];
  for (const arg of data) {
    if (arg && (arg.startsWith('http') || arg.startsWith('<http'))) {
      if (!thumbUrl) {
        thumbUrl = arg;
        if (thumbUrl.startsWith('<')) { thumbUrl = thumbUrl.substring(1); }
        if (thumbUrl.endsWith('>')) { thumbUrl = thumbUrl.slice(0, -1); }
      }
    } else if (arg) {
      if (notes) { notes += ' ' + arg.trim(); }
      else { notes = arg.trim(); }
    }
  }
  return { notes, thumbUrl };
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
    const args = extractArgs(data.slice(1));
    message.channel.send(placeholderText().join('\n'))
      .then(function(result) { panels.add(cmd, result, args.notes).save(); })
      .catch(function(error) { logger.error(error, message); });
  } else if (cmd === 'status-embed') {
    const args = extractArgs(data.slice(1));
    message.channel.send({ embeds: [placeholderEmbed(args.thumbUrl)] })
      .then(function(result) { panels.add(cmd, result, args.notes, args.thumbUrl).save(); })
      .catch(function(error) { logger.error(error, message); });
  } else {
    msgutil.reactUnknown(message);
  }
}
