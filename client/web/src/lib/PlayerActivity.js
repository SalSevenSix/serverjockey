import { RollingLog, humanDuration, shortISODateTimeString } from '$lib/util';
import { newGetRequest } from '$lib/sjgmsapi';
import { notifyError } from '$lib/notifications';


function extractInstances(queryResults) {
  let result = [];
  queryResults.lastevent.records.forEach(function(record) {
    if (!result.includes(record[1])) { result.push(record[1]); }
  });
  queryResults.events.records.forEach(function(record) {
    if (!result.includes(record[1])) { result.push(record[1]); }
  });
  return result;
}

function toLastEventMap(instances, data) {
  let result = {};
  instances.forEach(function(instance) {
    result[instance] = {};
  });
  data.records.forEach(function(record) {
    result[record[1]][record[2]] = record[3];
  });
  return result;
}

function newOnlineTracker() {
  let self = { current: 0, min: 0, max: 0 };
  self.bump = function() {
    self.current += 1;
    self.min = self.current;
    self.max = self.current;
  };
  self.login = function() {
    self.current += 1;
    if (self.current > self.max) { self.max = self.current; }
  };
  self.logout = function() {
    self.current -= 1;
    if (self.current < self.min) { self.min = self.current; }
  };
  return self;
}

function newDailyTracker(log, atfrom, atto) {
  let dayMillis = 24 * 60 * 60 * 1000;
  let self = { days: [] };
  let current = atfrom;
  while (current < atto) {
    let day = { sessions: 0, uptime: 0, atfrom: current, atto: current + dayMillis };
    // log.append(shortISODateTimeString(day.atfrom) + '   ' + shortISODateTimeString(day.atto));
    self.days.push(day);
    current += dayMillis;
  }
  self.session = function(login, logout) {
    self.days.forEach(function(day) {
      if (login >= day.atfrom && logout <= day.atto) {
        // log.append(shortISODateTimeString(day.atfrom) + ' >< ' + humanDuration(logout - login));
        day.uptime += logout - login;
        day.sessions += 1;
      } else if (logout >= day.atfrom && logout <= day.atto && login < day.atfrom) {
        // log.append(shortISODateTimeString(day.atfrom) + ' << ' + humanDuration(logout - day.atfrom));
        day.uptime += logout - day.atfrom;
        day.sessions += 1;
      } else if (login >= day.atfrom && login <= day.atto && logout > day.atto) {
        // log.append(shortISODateTimeString(day.atfrom) + ' >> ' + humanDuration(day.atto - login));
        day.uptime += day.atto - login;
        day.sessions += 1;
      } else if (login < day.atfrom && logout > day.atto) {
        // log.append(shortISODateTimeString(day.atfrom) + ' <> ' + humanDuration(dayMillis));
        day.uptime += dayMillis;
        day.sessions += 1;
      }
    });
  };
  return self;
}

export function extractActivity(queryResults) {
  let log = new RollingLog(1000);
  let data = queryResults.events;
  let instances = extractInstances(queryResults);
  let lastEventMap = toLastEventMap(instances, queryResults.lastevent);
  let dailyTrackers = {};
  let onlineTrackers = {};
  let entries = {};
  let entry = null;
  instances.forEach(function(instance) {  // Initialise entries
    entries[instance] = {};
    dailyTrackers[instance] = newDailyTracker(log, data.criteria.atfrom, data.criteria.atto);
    onlineTrackers[instance] = newOnlineTracker();
    Object.keys(lastEventMap[instance]).forEach(function(player) {
      if (lastEventMap[instance][player] === 'LOGIN') {
        entry = { at: data.criteria.atfrom, event: 'LOGIN', sessions: 1, uptime: 0 };
        entries[instance][player] = entry;
        onlineTrackers[instance].bump();
      }
    });
  });
  data.records.forEach(function(record) {  // Process event records to calculate uptime and session count
    let [at, instance, player, event] = record;
    if (entries[instance].hasOwnProperty(player)) {
      entry = entries[instance][player];
    } else {
      entry = { at: at, event: event, sessions: 0, uptime: 0 };
      if (event === 'LOGIN') {
        entry.sessions += 1;
        onlineTrackers[instance].login();
      }
      entries[instance][player] = entry;
    }
    if (event != entry.event) {
      if (event === 'LOGIN') {
        entry.sessions += 1;
        onlineTrackers[instance].login();
      } else if (entry.event === 'LOGIN') {
        /* log.append(shortISODateTimeString(entry.at) + '  ' + shortISODateTimeString(at) + ' '
                 + humanDuration(at - entry.at) + '   - ' + player); */
        entry.uptime += at - entry.at;
        dailyTrackers[instance].session(entry.at, at);
        onlineTrackers[instance].logout();
      }
      entry.at = at;
      entry.event = event;
    }
  });
  instances.forEach(function(instance) {  // Close off entries for logged in players
    Object.keys(entries[instance]).forEach(function(player) {
      entry = entries[instance][player];
      if (entry.event === 'LOGIN') {
        /* log.append(shortISODateTimeString(entry.at) + '  '
                 + shortISODateTimeString(data.criteria.atto) + ' '
                 + humanDuration(data.criteria.atto - entry.at)
                 + '  = ' + player); */
        entry.uptime += data.criteria.atto - entry.at;
        dailyTrackers[instance].session(entry.at, data.criteria.atto);
      }
    });
  });
  let results = {};
  instances.forEach(function(instance) {  // Generate report result object
    let total = { sessions: 0, uptime: 0 };
    let players = [];
    Object.keys(entries[instance]).forEach(function(player) {
      entry = entries[instance][player];
      total.sessions += entry.sessions;
      total.uptime += entry.uptime;
      players.push({ player: player, sessions: entry.sessions, uptime: entry.uptime });
    });
    players.forEach(function(player) {
      player.uptimepct = player.uptime / total.uptime;
    });
    players.sort(function(left, right) {
      return right.uptime - left.uptime;
    });
    let summary = { instance: instance, total: total, unique: players.length };
    summary.online = { min: onlineTrackers[instance].min, max: onlineTrackers[instance].max };
    let days = [];
    dailyTrackers[instance].days.forEach(function(day) {
      days.push({ atfrom: day.atfrom, atto: day.atto, sessions: day.sessions, uptime: day.uptime });
    });
    results[instance] = { summary: summary, players: players, days: days };
  });
  return { meta: { created: data.created, atfrom: data.criteria.atfrom, atto: data.criteria.atto,
           atrange: data.criteria.atto - data.criteria.atfrom, log: log.toText() }, results: results };
}

export function compactPlayers(players, limit=10) {
  if (limit >= players.length) return players;
  let result = [];
  let counter = limit - 1;
  let others = null;
  players.forEach(function(player) {
    if (counter > 0) {
      result.push(player);
      counter -= 1;
    } else {
      if (!others) { others = { player: 'OTHERS', sessions: 0, uptime: 0, uptimepct: 0.0 }; }
      others.sessions += player.sessions;
      others.uptime += player.uptime;
      others.uptimepct += player.uptimepct;
    }
  });
  if (others) { result.push(others); }
  return result;
}

async function queryFetch(url, errorMessage) {
  return await fetch(url, newGetRequest())
    .then(function(response) {
      if (!response.ok) throw new Error('Status: ' + response.status);
      return response.json();
    })
    .then(function(json) { return json; })
    .catch(function(error) { notifyError(errorMessage); });
}

export async function queryEvents(criteria) {
  let url = '/store/player/event?atfrom=' + criteria.atfrom + '&atto=' + criteria.atto;
  if (criteria.instance) { url += '&instance=' + criteria.instance; }
  return await queryFetch(url, 'Failed to query player events.');
}

export async function queryLastEvent(criteria) {
  let url = '/store/player/event?atgroup=max&atto=' + criteria.atfrom;
  if (criteria.instance) { url += '&instance=' + criteria.instance; }
  return await queryFetch(url, 'Failed to query last player event.');
}
