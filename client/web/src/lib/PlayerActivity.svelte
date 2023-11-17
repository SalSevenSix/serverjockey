<script>
  import { onMount, onDestroy, getContext } from 'svelte';
  import { queryEvents, queryLastEvent, extractActivity, compactPlayers, chunkPlayers } from '$lib/PlayerActivity';
  import { floatToPercent, humanDuration, shortISODateString, shortISODateTimeString } from '$lib/util';
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

  function chartDataPlayers(instance) {
    let players = compactPlayers(instance.players, 7);
    let labels = players.map(function(player) {
      return player.player.substring(0, 13);
    });
    let data = players.map(function(player) {
      return Math.round(player.uptimepct * 1000.0) / 10.0;
    });
    return {
      type: 'pie',
      data: { labels: labels, datasets: [{ label: ' % ', data: data }] },
      options: { plugins: { legend: { position: 'right' }}}
    }
  }

  function chartDataDays(instance) {
    let labels = instance.days.map(function(day) {
      return shortISODateString(day.atto);
    });
    let playerHours = instance.days.map(function(day) {
      return day.uptime / 3600000;
    });
    let sessions = instance.days.map(function(day) {
      return day.sessions;
    });
    return {
      type: 'line',
      data: { labels: labels,
              datasets: [{ label: 'player hours', data: playerHours },
                         { label: 'sessions', data: sessions }]}
    }
  }

  function queryActivity(criteria) {
    activity = null;
    results = {};
    Promise.all([queryLastEvent(criteria), queryEvents(criteria)]).then(function(data) {
      [results.lastevent, results.events] = data;
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
    {#if Object.keys(activity.results).length > 0}
      {#each Object.keys(activity.results) as instance}
        <div class="columns">
          <div class="column mt-0 pt-0">
            <table class="table is-thinner"><tbody>
              <tr><td></td><td></td><tr>
              <tr><td class="has-text-weight-bold"
                      title="Instance for reported player activity">Instance</td>
                  <td>{activity.results[instance].summary.instance}</td></tr>
              <tr><td class="has-text-weight-bold"
                      title="Number of unique players identified">Players</td>
                  <td>{activity.results[instance].summary.unique}</td></tr>
              <tr><td class="has-text-weight-bold"
                      title="Maximum recorded concurrent players">Players Max</td>
                  <td>{activity.results[instance].summary.online.max}</td></tr>
              <tr><td class="has-text-weight-bold"
                      title="Minimum recorded concurrent players">Players Min</td>
                  <td>{activity.results[instance].summary.online.min}</td></tr>
              <tr><td class="has-text-weight-bold"
                      title="Sum of time played by all players">Total Time</td>
                  <td>{humanDuration(activity.results[instance].summary.total.uptime)}</td></tr>
              <tr><td class="has-text-weight-bold"
                      title="Sum of player sessions (logins)">Total Sessions</td>
                  <td>{activity.results[instance].summary.total.sessions}</td></tr>
            </tbody></table>
          </div>
          <div class="column chart-container-players">
            <div><ChartCanvas data={chartDataPlayers(activity.results[instance])} /></div>
          </div>
        </div>
        <div class="block chart-container-days mb-3">
          <div><ChartCanvas data={chartDataDays(activity.results[instance])} /></div>
        </div>
        {#each chunkPlayers(activity.results[instance].players) as entryRows}
          <div class="columns">
            {#each entryRows as entryColumns}
              <div class="column is-one-third mt-0 mb-0 pt-0 pb-0"><table class="table is-thinner"><tbody>
                <tr><td>&nbsp;</td><td>&nbsp;</td></tr>
                {#each entryColumns as entry}
                  <tr>
                    <td class="word-break-all">{entry.player}</td>
                    <td class="online-column" title="{entry.sessions} sessions">{humanDuration(entry.uptime, 2)}</td>
                  </tr>
                {/each}
              </tbody><table></div>
            {/each}
          </div>
        {/each}
        <div class="block pb-3"></div>
      {/each}
    {:else}
      <div class="content">
        <p><i class="fa fa-triangle-exclamation fa-lg ml-3 mr-1"></i> No player activity found</p>
      </div>
    {/if}
  </div>
  {#if activity.meta.log}
    <div class="content">
      <pre class="pre">{activity.meta.log}</pre>
    </div>
  {/if}
{:else}
  <div class="content">
    <p><SpinnerIcon /> Loading Player Activity...<br /><br /></p>
  </div>
{/if}


<style>
  .chart-container-players div {
    max-width: 330px;
    margin: -70px auto -60px auto;
  }

  .chart-container-days {
    overflow-x: auto;
  }

  .chart-container-days div {
    max-width: 860px;
    min-width: 700px;
    margin: 0px auto 8px auto;
  }

  .online-column {
    white-space: nowrap;
    width: 10%;
  }
</style>
