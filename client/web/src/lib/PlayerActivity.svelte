<script>
  import { onMount, onDestroy, getContext } from 'svelte';
  import { queryInstance, queryEvents, queryLastEvent, extractActivity } from '$lib/PlayerActivity';
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
    let labels = instance.players.map(function(player) { return player.player; });
    let data = instance.players.map(function(player) {
      return Math.round((player.uptime / instance.summary.total) * 1000.0) / 10.0;
    });
    return {
      type: 'pie',
      data: {
        labels: labels,
        datasets: [{ label: ' % ', data: data }]
      },
      options: { plugins: { legend: { position: 'right' }}}
    }
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
        <p class="has-text-weight-bold">Players</p>
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
    {#each Object.keys(activity.results) as instance}
      <div class="columns">
        <div class="column">
          <table class="table is-thinner"><tbody>
            <tr><td class="has-text-weight-bold">Instance</td>
                <td>{activity.results[instance].summary.instance}</td></tr>
            <tr><td class="has-text-weight-bold">Unique Players</td>
                <td>{activity.results[instance].summary.unique}</td></tr>
            <tr><td class="has-text-weight-bold">Total Online</td>
                <td>{humanDuration(activity.results[instance].summary.total)}</td></tr>
          </tbody></table>
        </div>
        <div class="column">
          <div class="chart"><ChartCanvas data={chartData(activity.results[instance])} /></div>
        </div>
      </div>
      <div class="block">
        <table class="table"><tbody>
        {#each activity.results[instance].players as entry}
          <tr>
            <td>{entry.player}</td>
            <td>{humanDuration(entry.uptime, 2)}</td>
            <td>{entry.sessions}</td>
          </tr>
        {/each}
        </tbody><table>
      </div>
    {/each}
  </div>
{:else}
  <div class="content">
    <p><SpinnerIcon /> Loading Player Activity...<br /><br /></p>
  </div>
{/if}


<style>
  .chart {
    width: 330px;
    height: 330px;
    margin: -80px auto -80px 40px;
  }
</style>
