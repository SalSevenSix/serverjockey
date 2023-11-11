import { newGetRequest } from '$lib/sjgmsapi';
import { notifyError } from '$lib/notifications';

function toInstanceCreatedMap(iData) {
  let result = {};
  iData.records.forEach(function(record) {
    result[record[1]] = record[0];
  });
  return result;
}

export function extractActivity(iData, eData) {
  let entries = {};
  let entry = null;
  let createdMap = toInstanceCreatedMap(iData);
  eData.records.forEach(function(record) {
    let [at, instance, event] = record;
    if (entries.hasOwnProperty(instance)) {
      entry = entries[instance];
    } else {
      entry = { sessions: 0, uptime: 0 };
      entry.at = at;
      entry.from = createdMap[instance] > eData.criteria.atfrom ? createdMap[instance] : eData.criteria.atfrom;
      entry.event = event;
      if (event === 'STOPPED' || event === 'EXCEPTION') {
        entry.sessions += 1;
        entry.uptime += at - entry.from;   // TODO need to find when it actually started
      }
      entries[instance] = entry;
    }
    if (entry.event != event) {
      if (entry.event === 'STARTED' && (event === 'STOPPED' || event === 'EXCEPTION')) {
        entry.uptime += at - entry.at;
      }
      if (event === 'STARTED') {
        entry.sessions += 1;
      }
      entry.at = at;
      entry.event = event;
    }
  });
  let result = { created: eData.created, atfrom: eData.criteria.atfrom, atto: eData.criteria.atto,
                 atrange: eData.criteria.atto - eData.criteria.atfrom, instances: [] };
  Object.keys(entries).forEach(function(instance) {
    entry = entries[instance];
    if (entry.event === 'STARTED') {
      entry.uptime += eData.criteria.atto - entry.at;
    }
    let instanceResult = { instance: instance, created: createdMap[instance], sessions: entry.sessions };
    instanceResult.uptime = entry.uptime;
    instanceResult.range = eData.criteria.atto - entry.from;
    instanceResult.available = instanceResult.uptime / instanceResult.range;
    result.instances.push(instanceResult);
  });
  return result;
}

export async function queryInstance(criteria) {
  let url = '/store/instance';
  if (criteria.instance) { url += '?instance=' + criteria.instance; }
  return await fetch(url, newGetRequest())
    .then(function(response) {
      if (!response.ok) throw new Error('Status: ' + response.status);
      return response.json();
    })
    .then(function(json) { return json; })
    .catch(function(error) { notifyError('Failed to query instance.'); });
}

export async function queryEvents(criteria) {
  if (!criteria.atto) { criteria.atto = Date.now(); }
  if (!criteria.atfrom) { criteria.atfrom = criteria.atto - 2592000000; }  // 30 days
  let url = '/store/instance/event?events=STARTED,STOPPED,EXCEPTION';
  url += '&atfrom=' + criteria.atfrom + '&atto=' + criteria.atto;
  if (criteria.instance) { url += '&instance=' + criteria.instance; }
  return await fetch(url, newGetRequest())
    .then(function(response) {
      if (!response.ok) throw new Error('Status: ' + response.status);
      return response.json();
    })
    .then(function(json) { return json; })
    .catch(function(error) { notifyError('Failed to query instance events.'); });
}
