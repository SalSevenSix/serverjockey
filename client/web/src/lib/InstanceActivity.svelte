<script>
  import { onMount, onDestroy, getContext } from 'svelte';
  import { queryInstance, queryEvents, queryLastEvent, extractActivity } from '$lib/InstanceActivity';
  import { floatToPercent, humanDuration, shortISODateTimeString } from '$lib/util';
  import SpinnerIcon from '$lib/SpinnerIcon.svelte';
  import ChartCanvas from '$lib/ChartCanvas.svelte';

  const instance = getContext('instance');

  let objectUrls = [];
  let results = null;
  let activity = null;

  function showResults() {
    if (!activity) return;
    let blob = new Blob([JSON.stringify(results)], { type : 'text/plain;charset=utf-8' });
    let objectUrl = window.URL.createObjectURL(blob);
    objectUrls.push(objectUrl);
    window.open(objectUrl).focus();
  }

  function chartData(instance) {
    let upTime = Math.round(instance.available * 1000.0) / 10.0;
    return {
      type: 'pie',
      data: {
        labels: ['UP', 'DOWN'],
        datasets: [{
          label: ' % ',
          backgroundColor: ['#48C78E', '#F14668'],
          data: [upTime, 100.0 - upTime]
        }],
      },
      options: { plugins: { legend: { position: 'right' }}}
    };
  }

  function queryActivity(criteria) {
    activity = null;
    results = {};
    Promise.all([queryInstance(criteria), queryLastEvent(criteria), queryEvents(criteria)]).then(function(data) {
      [results.instances, results.lastevent, results.events] = data;
      activity = extractActivity(results);
    });
  }

  onMount(function() {
    let criteria = { instance: null };
    if (instance) { criteria.instance = instance.identity(); }
    criteria.atto = Date.now();
    criteria.atfrom = criteria.atto - 2592000000;  // 30 days
    queryActivity(criteria);
  });

  onDestroy(function() {
    objectUrls.forEach(function(objectUrl) {
      URL.revokeObjectURL(objectUrl);
    });
  });
</script>


{#if activity}
  <div class="block">
    <div class="columns">
      <div class="column is-2 mb-0 pb-0">
        <p class="has-text-weight-bold">
          {activity.results.length > 1 ? 'Instances' : 'Instance'}
        </p>
      </div>
      <div class="column is-10">
        <p>
          <a href={'#'} on:click|preventDefault={showResults}>
            results <i class="fa fa-up-right-from-square"></i></a>&nbsp;
          <span class="white-space-nowrap">from &nbsp;{shortISODateTimeString(activity.meta.atfrom)}&nbsp;</span>
          <span class="white-space-nowrap">to &nbsp;{shortISODateTimeString(activity.meta.atto)}&nbsp;</span>
          <span class="white-space-nowrap">({humanDuration(activity.meta.atrange)})</span>
        </p>
      </div>
    </div>
    {#each activity.results as entry}
      <div class="columns">
        <div class="column">
          <table class="table is-thinner"><tbody>
            <tr><td class="has-text-weight-bold">Name</td><td>{entry.instance}</td></tr>
            <tr><td class="has-text-weight-bold">Created</td><td>{shortISODateTimeString(entry.created)}</td></tr>
            <tr><td class="has-text-weight-bold">Range</td><td>{humanDuration(entry.range)}</td></tr>
            <tr><td class="has-text-weight-bold">Uptime</td><td>{humanDuration(entry.uptime)}</td></tr>
            <tr><td class="has-text-weight-bold">Available</td><td>{floatToPercent(entry.available)}</td></tr>
            <tr><td class="has-text-weight-bold">Sessions</td><td>{entry.sessions}</td></tr>
          </tbody></table>
        </div>
        <div class="column">
          <div class="chart"><ChartCanvas data={chartData(entry)} /></div>
        </div>
      </div>
    {/each}
  </div>
{:else}
  <div class="content">
    <p><SpinnerIcon /> Loading Instance Activity...<br /><br /></p>
  </div>
{/if}


<style>
  .chart {
    width: 280px;
    height: 280px;
    margin: -50px auto -50px 40px;
  }
</style>
