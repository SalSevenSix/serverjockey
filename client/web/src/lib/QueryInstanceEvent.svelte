<script>
  import { onMount, onDestroy } from 'svelte';
  import { notifyError } from '$lib/notifications';
  import { newGetRequest } from '$lib/sjgmsapi';
  import { floatToPercent, humanDuration, shortISODateTimeString } from '$lib/util';
  import SpinnerIcon from '$lib/SpinnerIcon.svelte';
  import ChartCanvas from '$lib/ChartCanvas.svelte';

  export let criteria;

  let objectUrls = [];
  let hasStore = null;
  let queryResult = null;
  let uptimeStats = null;

  function showQueryResult() {
    if (!queryResult) return;
    let blob = new Blob([JSON.stringify(queryResult)], { type : 'text/plain;charset=utf-8' });
    let objectUrl = window.URL.createObjectURL(blob);
    objectUrls.push(objectUrl);
    window.open(objectUrl).focus();
  }

  function buildInstanceChartData(entry) {
    let upTime = Math.round(entry.avail * 100.0 * 1000.0) / 1000.0;
    return {
      type: 'pie',
      data: {
        labels: ['UP', 'DOWN'],
        datasets: [{
          label: ' % ',
          borderColor: '#DBDBDB',
          backgroundColor: ['#48C78E', '#F14668'],
          data: [upTime, 100.0 - upTime]
        }]
      }
    };
  }

  function extractUptimeStats(data) {
    let entries = {};
    let entry = null;
    data.records.forEach(function(record) {
      let [at, instance, event] = record;
      if (entries.hasOwnProperty(instance)) {
        entry = entries[instance];
      } else {
        entry = { at: null, event: null, sessions: 0, uptime: 0 };
        if (event === 'STOPPED') {  // TODO what if exception was after started
          entry.sessions += 1;
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
        if (event === 'STARTED') {
          entry.sessions += 1;
        }
        entry.at = at;
        entry.event = event;
      }
    });
    let result = { created: data.created, atfrom: data.criteria.atfrom, atto: data.criteria.atto,
                   atrange: data.criteria.atto - data.criteria.atfrom, instances: [] };
    Object.keys(entries).forEach(function(instance) {
      entry = entries[instance];
      if (entry.event === 'STARTED') {
        entry.uptime += data.criteria.atto - entry.at;
      }
      result.instances.push({
        instance: instance, sessions: entry.sessions,
        uptime: entry.uptime, avail: entry.uptime / result.atrange });
    });
    return result;
  }

  export function queryInstanceEvent(qc) {
    if (!hasStore) return;
    if (!qc.atto) { qc.atto = Date.now(); }
    if (!qc.atfrom) { qc.atfrom = qc.atto - 2592000000; }  // 30 days
    let url = '/store/instance-event?events=STARTED,STOPPED,EXCEPTION';
    url += '&atfrom=' + qc.atfrom + '&atto=' + qc.atto;
    if (qc.instance) { url += '&instance=' + qc.instance; }
    fetch(url, newGetRequest())
      .then(function(response) {
        if (!response.ok) throw new Error('Status: ' + response.status);
        return response.json();
      })
      .then(function(json) {
        queryResult = json;
        uptimeStats = extractUptimeStats(json);
      })
      .catch(function(error) { notifyError('Failed to load query data.'); });
  }

  onMount(function() {
    fetch('/store', newGetRequest())
      .then(function(response) {
        hasStore = response.ok;
        if (criteria) { queryInstanceEvent(criteria); }
      })
      .finally(function() {
        if (hasStore === null) { hasStore = false; }
      });
  });

  onDestroy(function() {
    objectUrls.forEach(function(objectUrl) {
      URL.revokeObjectURL(objectUrl);
    });
  });
</script>


{#if uptimeStats}
  <div class="block">
    <div class="columns">
      <div class="column is-one-fifth mb-0 pb-0">
        <p><span class="has-text-weight-bold">Instance Uptime</span></p>
      </div>
      <div class="column is-four-fifths">
        <p>
          <a href={'#'} on:click|preventDefault={showQueryResult}>
            results <i class="fa fa-up-right-from-square"></i></a>&nbsp;
          <span class="white-space-nowrap">from &nbsp;{shortISODateTimeString(uptimeStats.atfrom)}&nbsp;</span>
          <span class="white-space-nowrap">to &nbsp;{shortISODateTimeString(uptimeStats.atto)}&nbsp;</span>
          <span class="white-space-nowrap">({humanDuration(uptimeStats.atrange)})</span>
        </p>
      </div>
    </div>
    {#each uptimeStats.instances as entry}
      <div class="columns">
        <div class="column is-one-third">
          <table class="table is-thinner"><tbody>
            <tr><td class="has-text-weight-bold">Instance</td><td>{entry.instance}</td></tr>
            <tr><td class="has-text-weight-bold">Sessions</td><td>{entry.sessions}</td></tr>
            <tr><td class="has-text-weight-bold">Uptime</td><td>{humanDuration(entry.uptime)}</td></tr>
            <tr><td class="has-text-weight-bold">Avail</td><td>{floatToPercent(entry.avail, 3)}</td></tr>
          </tbody></table>
        </div>
        <div class="column is-two-thirds">
          <div class="chart"><ChartCanvas data={buildInstanceChartData(entry)} /></div>
        </div>
      </div>
    {/each}
  </div>
{:else}
  <div class="content">
    {#if hasStore === false}
      <p><i class="fa fa-triangle-exclamation fa-lg"></i> Data Unavailable</p>
    {:else}
      <p><SpinnerIcon /> Loading...</p>
    {/if}
  </div>
{/if}


<style>
  .chart {
    width: 200px;
    height: 200px;
    margin: auto;
  }
</style>
