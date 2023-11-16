import { newGetRequest } from '$lib/sjgmsapi';
import { notifyError } from '$lib/notifications';


function toInstanceCreatedMap(data) {
  let result = {};
  data.records.forEach(function(record) {
    result[record[1]] = record[0];
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

export function extractActivity(queryResults) {
  let data = queryResults.events;
  let createdMap = toInstanceCreatedMap(queryResults.instances);
  let instances = Object.keys(createdMap);
  let lastEventMap = toLastEventMap(instances, queryResults.lastevent);
  let entries = {};
  let entry = null;
  instances.forEach(function(instance) {
    entries[instance] = {};
  });
  data.records.forEach(function(record) {  // Process event records to calculate uptime and session count
    let [at, instance, player, event] = record;
    if (entries[instance].hasOwnProperty(player)) {
      entry = entries[instance][player];
    } else {
      entry = { at: at, event: event, sessions: 0, uptime: 0 };
      entry.from = createdMap[instance] > data.criteria.atfrom ? createdMap[instance] : data.criteria.atfrom;
      if (event === 'LOGIN') {
        entry.sessions += 1;
      } else if (lastEventMap[instance].hasOwnProperty(player) && lastEventMap[instance][player] === 'LOGIN') {
        entry.sessions += 1;
        entry.uptime += at - entry.from;
      }
      entries[instance][player] = entry;
    }
    if (event != entry.event) {
      if (event === 'LOGIN') {
        entry.sessions += 1;
      } else if (entry.event === 'LOGIN') {
        entry.uptime += at - entry.at;
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
      }
    });
    Object.keys(lastEventMap[instance]).forEach(function(player) {
      if (lastEventMap[instance][player] === 'LOGIN' && !entries[instance].hasOwnProperty(player)) {
        entry = { sessions: 1 };
        entry.from = createdMap[instance] > data.criteria.atfrom ? createdMap[instance] : data.criteria.atfrom;
        entry.uptime = data.criteria.atto - entry.from;
        entries[instance][player] = entry;
      }
    });
  });
  let results = {};
  instances.forEach(function(instance) {
    results[instance] = { summary: { instance: instance }, players: [] };
    let totalUptime = 0;
    Object.keys(entries[instance]).forEach(function(player) {
      entry = entries[instance][player];
      totalUptime += entry.uptime;
      results[instance].players.push({ player: player, uptime: entry.uptime, sessions: entry.sessions });
    });
    results[instance].summary.unique = Object.keys(entries[instance]).length;
    results[instance].summary.total = totalUptime;
  });
  return { meta: { created: data.created, atfrom: data.criteria.atfrom, atto: data.criteria.atto,
           atrange: data.criteria.atto - data.criteria.atfrom }, results: results };
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

export async function queryInstance(criteria) {
  let url = '/store/instance';
  if (criteria.instance) { url += '?instance=' + criteria.instance; }
  return await queryFetch(url, 'Failed to query instance.');
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
