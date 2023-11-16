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
    result[instance] = null;
  });
  data.records.forEach(function(record) {
    result[record[1]] = record[2];
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
  instances.forEach(function(instance) {  // Initialise entries for all instances
    entry = { at: 0, event: null, sessions: 0, uptime: 0 };
    entry.from = createdMap[instance] > data.criteria.atfrom ? createdMap[instance] : data.criteria.atfrom;
    entries[instance] = entry;
  });
  data.records.forEach(function(record) {  // Process event records to calculate uptime and session count
    let [at, instance, event] = record;
    entry = entries[instance];
    if (!entry.event) {  // First event for instance
      entry.at = at;
      entry.event = event;
      if (event === 'STARTED') {
        entry.sessions += 1;
      } else if (lastEventMap[instance] === 'STARTED') {
        entry.sessions += 1;
        entry.uptime += at - entry.from;
      }
    }
    if (event != entry.event) {
      if (event === 'STARTED') {
        entry.sessions += 1;
      } else if (entry.event === 'STARTED') {
        entry.uptime += at - entry.at;
      }
      entry.at = at;
      entry.event = event;
    }
  });
  instances.forEach(function(instance) {  // Close off entries for running servers
    entry = entries[instance];
    if (!entry.event && lastEventMap[instance] === 'STARTED') {
      entry.uptime += data.criteria.atto - entry.from;
    } else if (entry.event === 'STARTED') {
      entry.uptime += data.criteria.atto - entry.at;
    }
  });
  // Generate report result object
  let results = [];
  instances.forEach(function(instance) {
    entry = entries[instance];
    let instanceResult = { instance: instance, created: createdMap[instance], sessions: entry.sessions };
    instanceResult.uptime = entry.uptime;
    instanceResult.range = data.criteria.atto - entry.from;
    instanceResult.available = instanceResult.uptime / instanceResult.range;
    results.push(instanceResult);
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
  let url = '/store/instance/event?events=STARTED,STOPPED,EXCEPTION';
  url += '&atfrom=' + criteria.atfrom + '&atto=' + criteria.atto;
  if (criteria.instance) { url += '&instance=' + criteria.instance; }
  return await queryFetch(url, 'Failed to query instance events.');
}

export async function queryLastEvent(criteria) {
  let url = '/store/instance/event?events=STARTED,STOPPED,EXCEPTION';
  url += '&atgroup=max&atto=' + criteria.atfrom;
  if (criteria.instance) { url += '&instance=' + criteria.instance; }
  return await queryFetch(url, 'Failed to query last instance event.');
}
