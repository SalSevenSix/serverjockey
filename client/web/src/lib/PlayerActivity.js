import { humanDuration, shortISODateTimeString } from '$lib/util';
import { newGetRequest } from '$lib/sjgmsapi';
import { notifyError } from '$lib/notifications';

const hourMillis = 60 * 60 * 1000;
const dayMillis = 24 * hourMillis;

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

function newIntervalTracker(atfrom, atto) {
  const self = {};
  const data = [];
  const intervalMillis = atto - atfrom > dayMillis ? dayMillis : hourMillis;
  let current = atto;
  while (current > atfrom) {
    data.push({
      atfrom: current - intervalMillis, atto: current,
      records: [], tracker: newOnlineTracker(),
      sessions: 0, uptime: 0 });
    current -= intervalMillis;
  }
  data.reverse();
  self.session = function(login, logout) {
    data.forEach(function(interval) {
      if (login >= interval.atfrom && logout <= interval.atto) {
        interval.records.push({ at: login, login: true });
        interval.records.push({ at: logout, login: false });
        interval.uptime += logout - login;
        interval.sessions += 1;
      } else if (logout >= interval.atfrom && logout <= interval.atto && login < interval.atfrom) {
        interval.records.push({ at: interval.atfrom, login: true });
        interval.records.push({ at: logout, login: false });
        interval.uptime += logout - interval.atfrom;
        interval.sessions += 1;
      } else if (login >= interval.atfrom && login <= interval.atto && logout > interval.atto) {
        interval.records.push({ at: login, login: true });
        interval.uptime += interval.atto - login;
        interval.sessions += 1;
      } else if (login < interval.atfrom && logout > interval.atto) {
        interval.records.push({ at: interval.atfrom, login: true });
        interval.uptime += intervalMillis;
        interval.sessions += 1;
      }
    });
  };
  self.results = function() {
    data.forEach(function(interval) {
      interval.records.sort(function(left, right) {
        return left.at - right.at;
      });
      interval.records.forEach(function(record) {
        if (record.login) {
          if (record.at === interval.atfrom) {
            interval.tracker.bump();
          } else {
            interval.tracker.login();
          }
        } else {
          interval.tracker.logout();
        }
      });
    });
    return {
      hours: Math.trunc(intervalMillis / hourMillis),
      data: data.map(function(interval) {
        return { atfrom: interval.atfrom, atto: interval.atto,
                 sessions: interval.sessions, uptime: interval.uptime,
                 min: interval.tracker.min, max: interval.tracker.max };
      })
    };
  };
  return self;
}

export function extractActivity(queryResults) {
  let data = queryResults.events;
  let instances = extractInstances(queryResults);
  let lastEventMap = toLastEventMap(instances, queryResults.lastevent);
  let intervalTrackers = {};
  let onlineTrackers = {};
  let entries = {};
  let entry = null;
  instances.forEach(function(instance) {  // Initialise entries
    entries[instance] = {};
    intervalTrackers[instance] = newIntervalTracker(data.criteria.atfrom, data.criteria.atto);
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
        entry.uptime += at - entry.at;
        intervalTrackers[instance].session(entry.at, at);
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
        entry.uptime += data.criteria.atto - entry.at;
        intervalTrackers[instance].session(entry.at, data.criteria.atto);
      }
    });
  });
  let results = {};
  instances.forEach(function(instance) {  // Generate report result object
    const total = { sessions: 0, uptime: 0 };
    const players = [];
    Object.keys(entries[instance]).forEach(function(player) {
      entry = entries[instance][player];
      total.sessions += entry.sessions;
      total.uptime += entry.uptime;
      players.push({ player: player, sessions: entry.sessions, uptime: entry.uptime });
    });
    if (total.sessions > 0) {
      players.forEach(function(player) {
        player.uptimepct = player.uptime / total.uptime;
      });
      players.sort(function(left, right) {
        return right.uptime - left.uptime;
      });
      const summary = { instance: instance, total: total, unique: players.length };
      summary.online = { min: onlineTrackers[instance].min, max: onlineTrackers[instance].max };
      const intervals = intervalTrackers[instance].results();
      results[instance] = { summary: summary, players: players, intervals: intervals };
    }
  });
  return { meta: { created: data.created, atfrom: data.criteria.atfrom, atto: data.criteria.atto,
           atrange: data.criteria.atto - data.criteria.atfrom }, results: results };
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

export async function queryEvents(instance, atfrom, atto) {
  let url = '/store/player/event?atfrom=' + atfrom + '&atto=' + atto;
  if (instance) { url += '&instance=' + instance; }
  return await queryFetch(url, 'Failed to query player events.');
}

export async function queryLastEvent(instance, atfrom) {
  let url = '/store/player/event?atgroup=max&atto=' + atfrom;
  if (instance) { url += '&instance=' + instance; }
  return await queryFetch(url, 'Failed to query last player event.');
}
