<script>
  import { onMount, onDestroy, getContext, tick } from 'svelte';
  import { queryEvents, queryLastEvent, extractActivity, compactPlayers } from '$lib/activity/PlayerActivity';
  import { chunkArray, humanDuration, shortISODateTimeString, ObjectUrls } from '$lib/util/util';
  import SpinnerIcon from '$lib/widget/SpinnerIcon.svelte';
  import ChartCanvas from '$lib/widget/ChartCanvas.svelte';

  const query = getContext('query');
  const objectUrls = new ObjectUrls();

  let processing = true;
  let results = null;
  let activity = null;

  $: query.blocker.notify('PlayerActivityProcessing', processing);

  function chartDataPlayers(instance) {
    const players = compactPlayers(instance.players, 7);
    const labels = players.map(function(player) {
      return player.player.padEnd(26);
    });
    const data = players.map(function(player) {
      return Math.round(player.uptimepct * 1000.0) / 10.0;
    });
    return {
      type: 'pie',
      data: { labels: labels, datasets: [{ label: ' % ', data: data }] },
      options: { plugins: { legend: { position: 'right', maxWidth: 135 }}}
    };
  }

  function chartDataIntervals(instance) {
    const data = { labels: {}, sessions: [], played: [], max: [] };
    instance.intervals.data.forEach(function(interval) {
      const dts = shortISODateTimeString(interval.atfrom);
      const label = instance.intervals.hours > 1 ? dts.substring(5, 10) : dts.substring(11, 16);
      data.labels[label] = interval.atfrom;
      data.sessions.push(interval.sessions);
      data.played.push(interval.uptime / 3600000);
      data.max.push(interval.max);
    });
    return {
      type: 'line',
      data: {
        labels: Object.keys(data.labels),
        datasets: [{ label: 'player hours', data: data.played },
                   { label: 'concurrent', data: data.max },
                   { label: 'sessions', data: data.sessions }]
      },
      options: {
        onClick: function(e, a) {
          const label = e.chart.data.labels[a[0].index];
          const atfrom = new Date(data.labels[label]);
          const [year, month, day] = [atfrom.getFullYear(), atfrom.getMonth(), atfrom.getDate()];
          if (label.includes('-')) {
            query.callups.setRange(new Date(year, month, day), new Date(year, month, day + 1));
          } else {
            query.callups.setRange(new Date(year, month, day - 15), new Date(year, month, day + 15));
          }
          query.execute();
        }
      }
    };
  }

  function queryActivity() {
    processing = true;
    const [instance, atrange] = [query.criteria.instance().identity(), query.criteria.atrange()];
    Promise.all([queryLastEvent(instance, atrange.atfrom), queryEvents(instance, atrange.atfrom, atrange.atto)])
      .then(function(data) {
        results = {};
        [results.lastevent, results.events] = data;
        activity = extractActivity(results);
      })
      .finally(function() { processing = false; });
  }

  query.onExecute('PlayerActivity', queryActivity);

  onMount(function() {
    tick().then(queryActivity);
  });

  onDestroy(function() {
    objectUrls.cleanup();
  });
</script>


{#if processing}
  <div class="content">
    <p><SpinnerIcon /> Loading Player Activity...</p>
  </div>
{:else if activity}
  <div class="columns">
    <div class="column is-2">
      <p class="has-text-weight-bold">Players</p>
    </div>
    <div class="column is-10">
      <p>
        <a href={'#'} on:click|preventDefault={function() { objectUrls.openObject(results); }}>
          results&nbsp;<i class="fa fa-up-right-from-square"></i></a>&nbsp;
        <span class="white-space-nowrap">from &nbsp;{shortISODateTimeString(activity.meta.atfrom)}&nbsp;</span>
        <span class="white-space-nowrap">to &nbsp;{shortISODateTimeString(activity.meta.atto)}&nbsp;</span>
        <span class="white-space-nowrap notranslate">({humanDuration(activity.meta.atrange)})</span>
      </p>
    </div>
  </div>
{/if}

{#if activity}
  {#if Object.keys(activity.results).length === 0}
    <div class="content pb-4">
      <p><i class="fa fa-triangle-exclamation fa-lg ml-3 mr-1"></i> No player activity found</p>
    </div>
  {:else}
    {#each Object.keys(activity.results) as instance}
      <div class="columns">
        <div class="column mt-0 pt-0">
          <table class="table is-thinner"><tbody>
            <tr><td class="label-column"></td><td></td><tr>
            <tr><td class="label-column has-text-weight-bold"
                    title="Instance for reported player activity">Instance</td>
                <td class="notranslate">{activity.results[instance].summary.instance}</td></tr>
            <tr><td class="label-column has-text-weight-bold"
                    title="Number of unique players identified">Players</td>
                <td class="notranslate">{activity.results[instance].summary.unique}</td></tr>
            <tr><td class="label-column has-text-weight-bold"
                    title="Maximum recorded concurrent players">Players Max</td>
                <td class="notranslate">{activity.results[instance].summary.online.max}</td></tr>
            <tr><td class="label-column has-text-weight-bold"
                    title="Minimum recorded concurrent players">Players Min</td>
                <td class="notranslate">{activity.results[instance].summary.online.min}</td></tr>
            <tr><td class="label-column has-text-weight-bold"
                    title="Sum of time played by all players">Total Time</td>
                <td class="notranslate">{humanDuration(activity.results[instance].summary.total.uptime)}</td></tr>
            <tr><td class="label-column has-text-weight-bold"
                    title="Sum of player sessions (logins)">Total Sessions</td>
                <td class="notranslate">{activity.results[instance].summary.total.sessions}</td></tr>
          </tbody></table>
        </div>
        <div class="column chart-container-players">
          {#if !processing}
            <div><ChartCanvas data={chartDataPlayers(activity.results[instance])} /></div>
          {/if}
        </div>
      </div>
      <div class="block chart-container-intervals">
        {#if !processing}
          <div><ChartCanvas data={chartDataIntervals(activity.results[instance])} /></div>
        {/if}
      </div>
      <div class="columns is-gapless mt-1">
        {#each chunkArray(compactPlayers(activity.results[instance].players, 45), 15, 3) as entryColumn}
          <div class="column is-one-third">
            <table class="table is-narrow"><tbody>
              <tr><td></td><td></td></tr>
              {#each entryColumn as entry}
                <tr title="{entry.sessions} sessions">
                  <td class="word-break-all player-column notranslate">{entry.player}</td>
                  <td class="white-space-nowrap online-column notranslate">{humanDuration(entry.uptime, 2)}</td>
                </tr>
              {/each}
            </tbody></table>
          </div>
        {/each}
      </div>
      <div class="block pb-2"></div>
    {/each}
  {/if}
{/if}


<style>
  .chart-container-players div {
    max-width: 330px;
    margin: -70px auto -60px auto;
  }

  .chart-container-intervals {
    overflow-x: auto;
  }

  .chart-container-intervals div {
    max-width: 860px;
    min-width: 700px;
    margin: 0px auto 8px auto;
  }

  .label-column {
    width: 40%;
    min-width: 90px;
  }

  .player-column {
    min-width: 130px;
  }

  .online-column {
    min-width: 90px;
  }
</style>
