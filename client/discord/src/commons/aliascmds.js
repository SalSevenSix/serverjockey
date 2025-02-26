import * as util from '../util.js';
import * as logger from '../logger.js';

export function alias($) {
  const [context, aliases, message, data] = [$.context, $.aliases, $.message, [...$.data]];
  if (!util.checkHasRole(message, context.config.ADMIN_ROLE)) return;
  const cmd = data.length > 0 ? data.shift() : 'list';
  if (cmd === 'list') {
    util.chunkStringArray(aliases.listText()).forEach(function(chunk) {
      message.channel.send('```\n' + chunk.join('\n') + '\n```');
    });
  } else if (cmd === 'find') {
    if (data.length != 1) return util.reactUnknown(message);
    let text = {};
    [aliases.findByKey(data[0]), aliases.findByName(data[0])].forEach(function(record) {
      if (record) { text[record.snowflake] = record.toString(); }
    });
    text = Object.values(text);
    text = text.length > 0 ? text.join('\n') : 'No Alias Found';
    message.channel.send('```\n' + text + '\n```');
  } else if (cmd === 'add') {
    if (data.length != 2) return util.reactUnknown(message);
    const [snowflake, name] = [util.toSnowflake(data[0]), data[1]];
    if (!snowflake) return util.reactError(message);
    context.client.users.fetch(snowflake)
      .then(function(user) {
        const discordid = user.tag.replaceAll('#', '');
        if (!aliases.add(snowflake, discordid, name)) return util.reactError(message);
        aliases.save();
        util.reactSuccess(message);
      })
      .catch(function(error) { logger.error(error, message); });
  } else if (cmd === 'remove') {
    if (data.length != 1) return util.reactUnknown(message);
    if (!aliases.remove(data[0])) return util.reactError(message);
    aliases.save();
    util.reactSuccess(message);
  } else {
    util.reactUnknown(message);
  }
}
