import * as util from '../util/util.js';
import * as logger from '../util/logger.js';
import * as msgutil from '../util/msgutil.js';

export function alias({ context, aliases, message, data }) {
  const [cmd, aliasid, name] = data.length > 0 ? data : ['list'];
  if (cmd === 'list') {
    msgutil.sendText(message, aliases.listText());
  } else if (cmd === 'find') {
    if (!aliasid) return msgutil.reactUnknown(message);
    let text = {};
    [aliases.findByKey(aliasid), aliases.findByName(aliasid)].forEach(function(record) {
      if (record) { text[record.snowflake] = record.toString(); }
    });
    text = Object.values(text);
    msgutil.sendText(message, text.length > 0 ? text : 'No Alias Found');
  } else if (cmd === 'add') {
    if (!aliasid || !name) return msgutil.reactUnknown(message);
    const snowflake = util.toSnowflake(aliasid);
    if (!snowflake) return msgutil.reactError(message);
    context.client.users.fetch(snowflake)
      .then(function(user) {
        const discordid = user.tag.replaceAll('#', '');
        if (!aliases.add(snowflake, discordid, name)) return msgutil.reactError(message);
        aliases.save();
        msgutil.reactSuccess(message);
      })
      .catch(function(error) { logger.error(error, message); });
  } else if (cmd === 'remove') {
    if (!aliasid) return msgutil.reactUnknown(message);
    if (!aliases.remove(aliasid)) return msgutil.reactError(message);
    aliases.save();
    msgutil.reactSuccess(message);
  } else {
    msgutil.reactUnknown(message);
  }
}
