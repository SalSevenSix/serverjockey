<script>
  import { onMount } from 'svelte';
  import { notifyError } from '$lib/notifications';
  import { newGetRequest } from '$lib/sjgmsapi';

  export let identity;

  let instance = identity;
  let atFrom = 1699449210000;
  let atTo = 1699449300000;
  let uptimeStats = 'loading...';

  function extractUptimeStats(data) {
    let entries = {};
    let entry = null;
    data.records.forEach(function(record) {
      let [at, instance, event] = record;
      if (entries.hasOwnProperty(instance)) {
        entry = entries[instance];
      } else {
        entry = { at: null, event: null, uptime: 0 };
        if (event === 'STOPPED') {
          entry.uptime += at - data.criteria.atfrom;
        }
        entry.at = at;
        entry.event = event;
        entries[instance] = entry;
      }
      if (entry.event != event) {
        if (entry.event === 'STARTED' && (event === 'STOPPED' || event === 'EXCEPTION')) {
          entry.uptime += at - entry.at;
        }
        entry.at = at;
        entry.event = event;
      }
    });
    Object.keys(entries).forEach(function(instance) {
      entry = entries[instance];
      if (entry.event === 'STARTED') {
        entry.uptime += data.criteria.atto - entry.at;
      }
    });
    let result = { created: data.created, duration: data.criteria.atto - data.criteria.atfrom, instances: [] };
    Object.keys(entries).forEach(function(instance) {
      let uptime = entries[instance].uptime;
      result.instances.push({ instance: instance, uptime: uptime, avail: uptime / result.duration });
    });
    return result;
  }

  onMount(function() {
    let url = '/store/instance-event?events=STARTED,STOPPED,EXCEPTION';
    url += '&atfrom=' + atFrom + '&atto=' + atTo;
    if (instance) { url += '&instance=' + instance; }
    fetch(url, newGetRequest())
      .then(function(response) {
        if (!response.ok) throw new Error('Status: ' + response.status);
        return response.json();
      })
      .then(function(json) {
        uptimeStats = JSON.stringify(extractUptimeStats(json));
      })
      .catch(function(error) { notifyError('Failed to query the store.'); });
  });
</script>


<div class="content">
  <p>{uptimeStats}</p>
</div>
