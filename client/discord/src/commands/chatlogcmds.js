import * as cutil from 'common/util/util';
import * as cstats from 'common/activity/chat';
import { emojis } from '../util/literals.js';
import * as logger from '../util/logger.js';
import * as util from '../util/util.js';
import * as http from '../util/http.js';
import * as msgutil from '../util/msgutil.js';

function formatHeader(results, tz) {
  const text = [['FROM ' + cutil.shortISODateTimeString(results.meta.atfrom, tz),
    ' TO ' + cutil.shortISODateTimeString(results.meta.atto, tz),
    ' (' + cutil.humanDuration(results.meta.atrange) + ')'].join('')];
  if (results.chat.length === 0) { text.push(emojis.nohelp + ' No chat found within time range'); }
  return text;
}

function formatVerbose(results, tz) {
  const text = formatHeader(results, tz);
  if (results.chat.length === 0) return text;
  results = results.chat.map(function(record) {
    if (!record.player) return '----- ' + record.at;
    return record.at + ' ' + record.player + ': ' + record.text;
  });
  text.push(...results);
  return text;
}

async function formatSummary(context, instance, results, tz) {
  const text = formatHeader(results, tz);
  if (results.chat.length === 0) return text;
  const chatlogClient = context.llmClient.newChatlog(context.instancesService.getModuleName(instance));
  results = results.chat.map(function(record) {
    if (!record.player) return null;
    return record.ats + ' ' + record.player + ': ' + record.text;
  });
  results = results.filter(function(line) { return line; });
  results = await chatlogClient.request(results);
  results = util.textToArray(results);
  text.push(...results);
  return text;
}

async function handleChatlog(context, instance, message, tz, atfrom, atto, player, format) {
  const fetched = await http.fetchJson(context, cstats.queryChats(instance, { atfrom, atto }, player).url);
  if (!fetched) throw new Error('Failed fetching chat data');
  const results = { meta: cstats.extractMeta(fetched),
    chat: cstats.extractResults(cstats.mergeResults({ chat: fetched }), tz) };
  if (format === 'VERBOSE') return msgutil.sendTextOrFile(message, formatVerbose(results, tz), 'chatlog', 2);
  msgutil.reactWait(message);
  const text = await formatSummary(context, instance, results, tz);
  msgutil.sendTextOrFile(message, text, 'chatlog', 2, false);
  await cutil.sleep(1000);
  msgutil.rmReacts(message, msgutil.reactSuccess, logger.error);
}

export function chatlog({ context, instance, message, data }) {
  const now = new Date();
  let [tz, atfrom, atto, player, format] = [null, null, null, null, 'VERBOSE'];
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
  handleChatlog(context, instance, message, tz, atfrom, atto, player, format)
    .catch(function(error) { logger.error(error, message); });
}
