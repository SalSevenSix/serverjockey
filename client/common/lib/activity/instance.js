function toInstanceCreatedMap(data) {
  const result = {};
  data.records.forEach(function(record) {
    result[record[1]] = record[0];
  });
  return result;
}

function toLastEventMap(instances, data) {
  const result = {};
  instances.forEach(function(instance) {
    result[instance] = null;
  });
  data.records.forEach(function(record) {
    result[record[1]] = record[2];
  });
  return result;
}

export function extractActivity(queryResults) {
  const now = Date.now();
  const data = queryResults.events;
  const uptimeAtto = data.criteria.atto > now ? now : data.criteria.atto;
  const createdMap = toInstanceCreatedMap(queryResults.instances);
  const instances = Object.keys(createdMap);
  const lastEventMap = toLastEventMap(instances, queryResults.lastevent);
  const entries = {};
  let entry = null;
  instances.forEach(function(instance) {  // Initialise entries for all instances
    entry = { at: 0, event: null, sessions: 0, uptime: 0 };
    entry.from = createdMap[instance] > data.criteria.atfrom ? createdMap[instance] : data.criteria.atfrom;
    entries[instance] = entry;
  });
  data.records.forEach(function(record) {  // Process event records to calculate uptime and session count
    const [at, instance, event] = record;
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
      entry.uptime += uptimeAtto - entry.from;
    } else if (entry.event === 'STARTED') {
      entry.uptime += uptimeAtto - entry.at;
    }
  });
  const results = [];
  instances.forEach(function(instance) {  // Generate report result object
    entry = entries[instance];
    const instanceResult = { instance: instance, created: createdMap[instance], sessions: entry.sessions };
    instanceResult.uptime = entry.uptime;
    instanceResult.range = data.criteria.atto - entry.from;
    instanceResult.available = instanceResult.uptime / instanceResult.range;
    results.push(instanceResult);
  });
  return { meta: { created: data.created, atfrom: data.criteria.atfrom, atto: data.criteria.atto,
           atrange: data.criteria.atto - data.criteria.atfrom }, results: results };
}

export function queryInstance(instance) {
  let url = '/store/instance';
  if (instance) { url += '?instance=' + instance; }
  return { url: url, error: 'Failed to query instance.' };
}

export function queryEvents(instance, atfrom, atto) {
  let url = '/store/instance/event';
  url += '?atfrom=' + atfrom + '&atto=' + atto;
  if (instance) { url += '&instance=' + instance; }
  url += '&events=STARTED,STOPPED,EXCEPTION';
  return { url: url, error: 'Failed to query instance events.' };
}

export function queryLastEvent(instance, atfrom) {
  let url = '/store/instance/event';
  url += '?atto=' + atfrom;
  if (instance) { url += '&instance=' + instance; }
  url += '&events=STARTED,STOPPED,EXCEPTION&atgroup=max';
  return { url: url, error: 'Failed to query last instance event.' };
}
