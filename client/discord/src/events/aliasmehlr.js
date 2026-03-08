import * as cutil from 'common/util/util';
import { emojis } from '../util/literals.js';

export function newAliasmeHandler(instance, channels, aliases) {
  return function(text, name) {
    if (!name || !text) return;
    const alias = aliases.aliasmeCheck(name, text);
    if (!alias) return;
    aliases.save();
    cutil.sleep(500).then(function() {
      const resolved = channels.resolve();
      const channel = resolved.chat ? resolved.chat : resolved.login;
      if (!channel) return;
      channel.send('`' + instance + '` ' + emojis.link + ' ' + alias.name + ' is alias of <@' + alias.snowflake + '>');
    });
  };
}
