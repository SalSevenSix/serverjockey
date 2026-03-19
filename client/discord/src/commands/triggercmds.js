import * as util from '../util/util.js';
import * as logger from '../util/logger.js';
import * as msgutil from '../util/msgutil.js';

function subsHelpText() {
  return [
    'Use the following keywords to substitute values in messages...',
    '{n}          : new line',
    '{!}          : bot command character(s)',
    '{player}     : quoted player "name", suitable for commands',
    '{playername} : just the player name',
    '{atmember}   : member @name, will ping',
    '{member}     : member name only, no ping',
    '{instance}   : instance name',
    '{channel}    : channel name',
    '{event}      : event name'
  ];
}

async function handleAdd(context, triggers, message, data) {
  const args = [];
  for (const arg of util.clobCommandLine(data)) {
    const [key, value] = arg.split('=');
    if (value && key.includes('role')) {
      const snowflake = util.toRoleId(value);
      if (!snowflake) throw new Error('Invalid role id: ' + value);
      const role = await message.guild.roles.fetch(snowflake);
      if (!role) throw new Error('Role not found: ' + value);
      args.push(key + '=' + JSON.stringify({ snowflake: snowflake, name: role.name }));
    } else if (value && key.includes('channel')) {
      const snowflake = util.toChannelId(value);
      if (!snowflake) throw new Error('Invalid channel id: ' + value);
      const channel = await context.channels.fetch(snowflake, message.guild.channels);
      if (!channel) throw new Error('Channel not found: ' + value);
      args.push(key + '=' + JSON.stringify({ snowflake: snowflake, name: channel.name }));
    } else {
      args.push(arg);
    }
  }
  if (triggers.add(args)) { triggers.save(); }
  else { throw new Error('Failed adding new trigger'); }
}

export function trigger({ context, triggers, message, data }) {
  const cmd = data.length > 0 ? data[0] : 'list';
  if (cmd === 'list') {
    msgutil.sendText(message, triggers.listText());
  } else if (cmd === 'subs') {
    msgutil.sendText(message, subsHelpText());
  } else if (cmd === 'add' || cmd.startsWith('on-')) {
    handleAdd(context, triggers, message, cmd === 'add' ? data.slice(1) : data)
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
