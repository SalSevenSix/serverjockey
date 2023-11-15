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

export function extractActivity(iData, eData, lData) {
  let entries = {};
  let entry = null;
  let createdMap = toInstanceCreatedMap(iData);
  let instances = Object.keys(createdMap);
  let lastEventMap = toLastEventMap(instances, lData);
  instances.forEach(function(instance) {  // Initialise entries for all instances
    entry = { at: 0, event: null, sessions: 0, uptime: 0 };
    entry.from = createdMap[instance] > eData.criteria.atfrom ? createdMap[instance] : eData.criteria.atfrom;
    entries[instance] = entry;
  });
  eData.records.forEach(function(record) {  // Process event records to calculate uptime and session count
    let [at, instance, event] = record;
    entry = entries[instance];
    if (!entry.event) {
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
      entry.uptime += eData.criteria.atto - entry.from;
    } else if (entry.event === 'STARTED') {
      entry.uptime += eData.criteria.atto - entry.at;
    }
  });
  // Generate report result object
  let result = { created: eData.created, atfrom: eData.criteria.atfrom, atto: eData.criteria.atto,
                 atrange: eData.criteria.atto - eData.criteria.atfrom, instances: [] };
  instances.forEach(function(instance) {
    entry = entries[instance];
    let resultEntry = { instance: instance, created: createdMap[instance], sessions: entry.sessions };
    resultEntry.uptime = entry.uptime;
    resultEntry.range = eData.criteria.atto - entry.from;
    resultEntry.available = resultEntry.uptime / resultEntry.range;
    result.instances.push(resultEntry);
  });
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
