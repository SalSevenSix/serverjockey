import * as cutil from 'common/util/util';
import * as cstats from 'common/activity/chat';
import * as logger from '../util/logger.js';
import * as util from '../util/util.js';
import * as msgutil from '../util/msgutil.js';

function formatHeader(results, tzFlag) {
  const text = [['FROM ' + cutil.shortISODateTimeString(results.meta.atfrom, tzFlag),
    ' TO ' + cutil.shortISODateTimeString(results.meta.atto, tzFlag),
    ' (' + cutil.humanDuration(results.meta.atrange) + ')'].join('')];
  if (results.chat.length === 0) { text.push('No chat found within time range'); }
  return text;
}

async function formatSummary(context, instance, results, tzFlag) {
  const gamename = context.instancesService.getModuleName(instance);
  const text = formatHeader(results, tzFlag);
  if (results.chat.length === 0) return text;
  results = results.chat.map(function(record) {
    if (!record.player) return null;
    return record.ats + ' ' + record.player + ': ' + record.text;
  });
  results = results.filter(function(line) { return line; });
  results = results.join('\n');
  results = await context.llmClient.chatlog({ input: results, gamename: gamename });
  results = util.textToArray(results);
  text.push(...results);
  return text;
}

function formatVerbose(results, tzFlag) {
  const text = formatHeader(results, tzFlag);
  if (results.chat.length === 0) return text;
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
      if (format === 'VERBOSE') {
        msgutil.sendTextOrFile(message, formatVerbose(results, tz), 'chat');
      } else if (format === 'SUMMARY') {
        msgutil.reactWait(message);
        formatSummary(context, instance, results, tz)
          .then(function(text) {
            msgutil.rmReacts(message, msgutil.reactSuccess, logger.error);
            msgutil.sendTextOrFile(message, text, 'chat', 3, false);
          });
      } else {
        msgutil.sendText(message, 'Invalid arguments');
      }
    });
}
