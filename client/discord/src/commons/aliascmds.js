import * as util from '../util/util.js';
import * as logger from '../util/logger.js';
import * as msgutil from '../util/msgutil.js';

export function alias({ context, aliases, message, data }) {
  if (!util.checkHasRole(message, context.config.ADMIN_ROLE)) return;
  const [cmd, aliasid, name] = data.length > 0 ? data : ['list'];
  if (cmd === 'list') {
    msgutil.sendText(message, aliases.listText());
  } else if (cmd === 'find') {
    if (!aliasid) return util.reactUnknown(message);
    let text = {};
    [aliases.findByKey(aliasid), aliases.findByName(aliasid)].forEach(function(record) {
      if (record) { text[record.snowflake] = record.toString(); }
    });
    text = Object.values(text);
    msgutil.sendText(message, text.length > 0 ? text : 'No Alias Found');
  } else if (cmd === 'add') {
    if (!aliasid || !name) return util.reactUnknown(message);
    const snowflake = util.toSnowflake(aliasid);
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
    if (!aliasid) return util.reactUnknown(message);
    if (!aliases.remove(aliasid)) return util.reactError(message);
    aliases.save();
    util.reactSuccess(message);
  } else {
    util.reactUnknown(message);
  }
}
