import * as cutil from 'common/util/util';
import * as istats from 'common/activity/instance';
import * as pstats from 'common/activity/player';
import * as logger from '../util/logger.js';
import * as http from '../util/http.js';
import * as msgutil from '../util/msgutil.js';

async function handleInstance(context, instance, message, format, tz, atfrom, atto) {
  const fetched = await Promise.all([
    http.fetchJson(context, istats.queryInstance(instance).url),
    http.fetchJson(context, istats.queryLastEvent(instance, atfrom).url),
    http.fetchJson(context, istats.queryEvents(instance, atfrom, atto).url)]);
  if (!cutil.checkArray(fetched, 3)) throw new Error('Failed fetching instance data');
  let results = {};
  [results.instances, results.lastevent, results.events] = fetched;
  results = istats.extractActivity(results);
  results = { meta: results.meta, summary: results.results[0] };
  if (format === 'JSON') return msgutil.sendTextOrFile(message, JSON.stringify(results, null, 2), 'activity');
  const text = [];
  text.push(['FROM ' + cutil.shortISODateTimeString(results.meta.atfrom, tz),
    ' TO ' + cutil.shortISODateTimeString(results.meta.atto, tz),
    ' (' + cutil.humanDuration(results.meta.atrange) + ')'].join(''));
  text.push('CREATED ' + cutil.shortISODateTimeString(results.summary.created, tz));
  text.push(['TOTAL sessions:' + results.summary.sessions,
    ' available:' + cutil.floatToPercent(results.summary.available),
    ' uptime:' + cutil.humanDuration(results.summary.uptime)].join(''));
  msgutil.sendText(message, text);
}

async function handlePlayer(context, instance, message, format, tz, atfrom, atto, player, limit, aliases) {
  const fetched = await Promise.all([
    http.fetchJson(context, pstats.queryLastEvent(instance, atfrom, player).url),
    http.fetchJson(context, pstats.queryEvents(instance, atfrom, atto, player).url)]);
  if (!cutil.checkArray(fetched, 2)) throw new Error('Failed fetching player data');
  let results = {};
  [results.lastevent, results.events] = fetched;
  results = pstats.extractActivity(results);
  const instanceResults = cutil.hasProp(results.results, instance) ? results.results[instance] : null;
  results = { meta: results.meta, summary: null, players: null };
  if (instanceResults) {
    results.summary = instanceResults.summary;
    results.players = instanceResults.players.map(function(record) {
      const playerAlias = aliases.findByName(record.player);
      record.discordid = playerAlias ? playerAlias.discordid : null;
      return record;
    });
  }
  if (format === 'JSON') return msgutil.sendTextOrFile(message, JSON.stringify(results, null, 2), 'activity');
  const text = [];
  text.push(['FROM ' + cutil.shortISODateTimeString(results.meta.atfrom, tz),
    ' TO ' + cutil.shortISODateTimeString(results.meta.atto, tz),
    ' (' + cutil.humanDuration(results.meta.atrange) + ')'].join(''));
  if (instanceResults) {
    text.push(['TOTAL unique:' + results.summary.unique +
      ' concurrent:' + results.summary.online.max +
      ' sessons:' + results.summary.total.sessions +
      ' played:' + cutil.humanDuration(results.summary.total.uptime)].join(''));
    if (limit && !player) { results.players = pstats.compactPlayers(results.players, limit); }
    const plen = Math.max(10, 2 + results.players.reduce(function(a, b) {
      return a.player.length > b.player.length ? a : b;
    }).player.length);
    results = results.players.map(function(record, index) {
      let line = (index + 1).toString().padStart(2, '0');
      line += ' ' + record.player.padEnd(plen);
      line += cutil.humanDuration(record.uptime, 'hm').padEnd(9);
      if (record.discordid) { line += ' @' + record.discordid; }
      return line.trim();
    });
    text.push(...results);
  } else {
    text.push('No player activity found');
  }
  msgutil.sendText(message, text);
}

export function activity({ context, aliases, instance, message, data }) {
  const now = new Date();
  let [tz, atfrom, atto, player, limit, format, query] = [null, null, null, null, 11, 'TEXT', 'player'];
  data.forEach(function(arg) {
    if (arg === 'instance') { query = arg; }
    else if (arg.startsWith('tz=')) { tz = arg.substring(3); }
    else if (arg.startsWith('player=')) { player = arg.substring(7); }
    else if (arg.startsWith('limit=')) { limit = parseInt(arg.substring(6), 10); }
    else if (arg.startsWith('format=')) { format = arg.substring(7).toUpperCase(); }
  });
  if (!['TEXT', 'JSON'].includes(format)) return msgutil.sendText(message, 'Invalid format');
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
  if (!atfrom) { atfrom = atto - 2592000000; }
  else if (atfrom < 0) { atfrom = atto + atfrom; }
  if (!tz) { tz = true; }
  if (query === 'instance') {
    handleInstance(context, instance, message, format, tz, atfrom, atto)
      .catch(function(error) { logger.error(error, message); });
  } else if (query === 'player') {
    handlePlayer(context, instance, message, format, tz, atfrom, atto, player, limit, aliases)
      .catch(function(error) { logger.error(error, message); });
  }
}
