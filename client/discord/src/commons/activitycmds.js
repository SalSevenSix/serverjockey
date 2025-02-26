import * as cutil from 'common/util/util';
import * as istats from 'common/activity/instance';
import * as pstats from 'common/activity/player';
import * as util from '../util.js';

/* eslint-disable max-lines-per-function */
export function activity($) {
  const [context, httptool, aliases, instance, message, data] = [
    $.context, $.httptool, $.aliases, $.instance, $.message, $.data];
  if (!util.checkHasRole(message, context.config.ADMIN_ROLE)) return;
  const [baseurl, now] = [context.config.SERVER_URL, new Date()];
  let [tz, atto, atfrom, player, limit, format, query] = [null, null, null, null, 11, 'TEXT', 'player'];
  data.forEach(function(arg) {
    if (arg === 'instance') { query = arg; }
    else if (arg.startsWith('tz=')) { tz = arg.substring(3); }
    else if (arg.startsWith('player=')) { player = arg.substring(7); }
    else if (arg.startsWith('limit=')) { limit = parseInt(arg.substring(6), 10); }
    else if (arg.startsWith('format=')) { format = arg.substring(7).toUpperCase(); }
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
  if (!atfrom) { atfrom = atto - 2592000000; }
  else if (atfrom < 0) { atfrom = atto + atfrom; }
  if (!tz) { tz = true; }
  let [results, text] = [{}, ['Invalid arguments']];
  if (query === 'instance') {
    Promise.all([
      httptool.getJson(istats.queryInstance(instance), baseurl),
      httptool.getJson(istats.queryLastEvent(instance, atfrom), baseurl),
      httptool.getJson(istats.queryEvents(instance, atfrom, atto), baseurl)])
      .then(function(promdata) {
        [results.instances, results.lastevent, results.events] = promdata;
        results = istats.extractActivity(results);
        results = { meta: results.meta, summary: results.results[0] };
        if (format === 'TEXT') {
          text = [];
          text.push(['FROM ' + cutil.shortISODateTimeString(results.meta.atfrom, tz),
            ' TO ' + cutil.shortISODateTimeString(results.meta.atto, tz),
            ' (' + cutil.humanDuration(results.meta.atrange) + ')'].join(''));
          text.push('CREATED ' + cutil.shortISODateTimeString(results.summary.created, tz));
          text.push(['TOTAL sessions:' + results.summary.sessions,
            ' available:' + cutil.floatToPercent(results.summary.available),
            ' uptime:' + cutil.humanDuration(results.summary.uptime)].join(''));
        } else if (format === 'JSON') {
          text = [JSON.stringify(results)];
        }
        message.channel.send('```\n' + text.join('\n') + '\n```');
      });
  } else if (query === 'player') {
    Promise.all([
      httptool.getJson(pstats.queryLastEvent(instance, atfrom, player), baseurl),
      httptool.getJson(pstats.queryEvents(instance, atfrom, atto, player), baseurl)])
      .then(function(promdata) {
        [results.lastevent, results.events] = promdata;
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
        if (format === 'TEXT') {
          text = [];
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
        } else if (format === 'JSON') {
          text = [JSON.stringify(results)];
        }
        util.chunkStringArray(text).forEach(function(chunk) {
          message.channel.send('```\n' + chunk.join('\n') + '\n```');
        });
      });
  }
}
/* eslint-enable max-lines-per-function */
