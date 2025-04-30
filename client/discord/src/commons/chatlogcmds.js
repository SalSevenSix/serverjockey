import * as cutil from 'common/util/util';
import * as cstats from 'common/activity/chat';
import * as msgutil from '../util/msgutil.js';

function formatVerbose(results, tzFlag) {
  const text = [];
  text.push(['FROM ' + cutil.shortISODateTimeString(results.meta.atfrom, tzFlag),
    ' TO ' + cutil.shortISODateTimeString(results.meta.atto, tzFlag),
    ' (' + cutil.humanDuration(results.meta.atrange) + ')'].join(''));
  results = results.chat.map(function(record) {
    if (!record.player) return '----- ' + record.at;
    return record.at + ' ' + record.player + ': ' + record.text;
  });
  text.push(...results);
  return text;
}

export function chatlog({ context, httptool, instance, message, data }) {
  if (!msgutil.checkHasRole(message, context.config.ADMIN_ROLE)) return;
  const [baseurl, now] = [context.config.SERVER_URL, new Date()];
  let [tz, atto, atfrom, player, format] = [null, null, null, null, 'VERBOSE'];
  data.forEach(function(arg) {
    if (arg === 'summary') { format = 'SUMMARY'; }
    else if (arg.startsWith('tz=')) { tz = arg.substring(3); }
    else if (arg.startsWith('player=')) { player = arg.substring(7); }
  });
  data.forEach(function(arg) {
    if (arg.startsWith('to=')) {
      atto = arg.substring(3);
      atto = ['LH', 'LD', 'LM', 'TM'].includes(atto)
        ? cutil.presetDate(now, atto, tz).getTime()
        : cutil.parseDateToMillis(atto, tz);
    } else if (arg.startsWith('from=')) {
      atfrom = arg.substring(5);
      atfrom = atfrom && ['d', 'h', 'm', 's'].includes(atfrom.slice(-1).toLowerCase())
        ? 0 - cutil.rangeCodeToMillis(atfrom)
        : cutil.parseDateToMillis(atfrom, tz);
    }
  });
  if (!atto) { atto = now.getTime(); }
  if (!atfrom) { atfrom = atto - 21600000; }
  else if (atfrom < 0) { atfrom = atto + atfrom; }
  if (!tz) { tz = true; }
  httptool.getJson(cstats.queryChats(instance, { atfrom, atto }, player), baseurl)
    .then(function(chatdata) {
      const results = { meta: cstats.extractMeta(chatdata),
        chat: cstats.extractResults(cstats.mergeResults({ chat: chatdata }), tz) };
      let text = 'Invalid arguments';
      if (format === 'VERBOSE') { text = formatVerbose(results, tz); }
      else if (format === 'SUMMARY') { text = 'Chat summary not supported yet'; }
      msgutil.sendTextOrFile(message, text, 'chat');
    });
}
