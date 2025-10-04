import * as util from '../util/util.js';
import * as logger from '../util/logger.js';
import * as msgutil from '../util/msgutil.js';

async function handleAdd(triggers, message, data) {
  const args = [];
  for (const arg of util.clobCommandLine(data)) {
    const [key, value] = arg.split('=');
    if (value && key.includes('role')) {
      const snowflake = util.toSnowflake(value, '<@&');
      if (!snowflake) throw new Error('Invalid role id: ' + value);
      const role = await message.guild.roles.fetch(snowflake);
      if (!role) throw new Error('Role not found: ' + value);
      args.push(key + '=' + JSON.stringify({ snowflake: snowflake, name: role.name }));
    } else if (value && key.includes('channel')) {
      const snowflake = util.toSnowflake(value, '<#');
      if (!snowflake) throw new Error('Invalid channel id: ' + value);
      const channel = await message.guild.channels.fetch(snowflake);
      if (!channel) throw new Error('Channel not found: ' + value);
      args.push(key + '=' + JSON.stringify({ snowflake: snowflake, name: channel.name }));
    } else {
      args.push(arg);
    }
  }
  if (triggers.add(args)) { triggers.save(); }
  else { throw new Error('Failed adding new trigger'); }
}

export function trigger({ triggers, message, data }) {
  const cmd = data.length > 0 ? data[0] : 'list';
  if (cmd === 'list') {
    msgutil.sendText(message, triggers.listText());
  } else if (cmd === 'add') {
    handleAdd(triggers, message, data.slice(1))
      .then(function() { msgutil.reactSuccess(message); })
      .catch(function(error) { logger.error(error, message); });
  } else if (cmd === 'remove') {
    if (data.length < 2) return msgutil.reactUnknown(message);
    if (!triggers.remove(data[1])) return msgutil.reactError(message);
    triggers.save();
    msgutil.reactSuccess(message);
  } else {
    msgutil.reactUnknown(message);
  }
}
