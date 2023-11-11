<script>
  import { onMount, onDestroy } from 'svelte';
  import { queryInstance, queryEvents, extractActivity } from '$lib/InstanceActivity';
  import { floatToPercent, humanDuration, shortISODateTimeString } from '$lib/util';
  import SpinnerIcon from '$lib/SpinnerIcon.svelte';
  import ChartCanvas from '$lib/ChartCanvas.svelte';

  export let criteria;

  let objectUrls = [];
  let instanceResults = null;
  let eventResults = null;
  let activity = null;

  $: if (instanceResults && eventResults) { onResults(); }
  function onResults() {
    activity = extractActivity(instanceResults, eventResults);
  }

  function showResults() {
    if (!activity) return;
    let results = { instances: instanceResults, events: eventResults };
    let blob = new Blob([JSON.stringify(results)], { type : 'text/plain;charset=utf-8' });
    let objectUrl = window.URL.createObjectURL(blob);
    objectUrls.push(objectUrl);
    window.open(objectUrl).focus();
  }

  function chartData(entry) {
    let upTime = Math.round(entry.available * 1000.0) / 10.0;
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

  export function queryActivity(queryCriteria) {
    activity = null;
    instanceResults = null;
    eventResults = null;
    queryInstance(queryCriteria).then(function(results) { instanceResults = results; });
    queryEvents(queryCriteria).then(function(results) { eventResults = results; });
  }

  onMount(function() {
    if (criteria) { queryActivity(criteria); }
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
      <div class="column is-one-fifth mb-0 pb-0">
        <p><span class="has-text-weight-bold">
          {eventResults.criteria.instance ? 'Instance' : 'Instances'}
        </span></p>
      </div>
      <div class="column is-four-fifths">
        <p>
          <a href={'#'} on:click|preventDefault={showResults}>
            results <i class="fa fa-up-right-from-square"></i></a>&nbsp;
          <span class="white-space-nowrap">from &nbsp;{shortISODateTimeString(activity.atfrom)}&nbsp;</span>
          <span class="white-space-nowrap">to &nbsp;{shortISODateTimeString(activity.atto)}&nbsp;</span>
          <span class="white-space-nowrap">({humanDuration(activity.atrange)})</span>
        </p>
      </div>
    </div>
    {#each activity.instances as entry}
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
    width: 220px;
    height: 220px;
    margin: auto;
  }
</style>
