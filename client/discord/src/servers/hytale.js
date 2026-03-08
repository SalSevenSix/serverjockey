import * as cutil from 'common/util/util';
import * as msgutil from '../util/msgutil.js';
import * as helptext from '../system/helptext.js';
import * as commons from '../system/commons.js';

export const startup = commons.startupAll;
export const { status, server, auto, log, getconfig, setconfig, players, send, say, chat,
  channel, aliasme, alias, reward, trigger, activity, chatlog } = commons;

export const help = helptext.newServerHelpBuilder()
  .title('HYTALE COMMANDS')
  .addServer().addPlayers().add([
    'player "{name}" group-true {group}  : Add player to group',
    'player "{name}" group-false {group} : Remove player from group'])
  .addSay().addChat().addSend().addChannel().addAliasme().addAlias()
  .addReward().addTrigger().addActivity().addChatlog()
  .next()
  .addConfig(['cmdargs', 'Mods', 'Settings', 'Permissions', 'Whitelist', 'Bans', 'Memories', 'Warps'])
  .build();

export function player({ httptool, aliases, message, data }) {
  if (data.length < 3) return msgutil.reactUnknown(message);
  const cmd = data[1];
  let url = '/console/perm/players/' + cutil.urlSafeB64encode(aliases.resolveName(data[0]));
  if (cmd === 'group-true') { url += '/groups/add'; }
  else if (cmd === 'group-false') { url += '/groups/remove'; }
  else { return msgutil.reactUnknown(message); }
  const body = { group: data[2] };
  httptool.doPost(url, body);
}
