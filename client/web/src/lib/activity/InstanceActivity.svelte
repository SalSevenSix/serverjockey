<script>
  import { onMount, onDestroy, getContext, tick } from 'svelte';
  import { queryInstance, queryEvents, queryLastEvent, extractActivity } from '$lib/activity/InstanceActivity';
  import { floatToPercent, humanDuration, shortISODateTimeString, ObjectUrls } from '$lib/util/util';
  import SpinnerIcon from '$lib/widget/SpinnerIcon.svelte';
  import ChartCanvas from '$lib/widget/ChartCanvas.svelte';

  const query = getContext('query');
  const objectUrls = new ObjectUrls();

  let processing = true;
  let results = null;
  let activity = null;

  $: query.blocker.notify('InstanceActivityProcessing', processing);

  function chartData(instance) {
    const upTime = Math.round(instance.available * 1000.0) / 10.0;
    return {
      type: 'pie',
      data: {
        labels: ['UP'.padEnd(26), 'DOWN'.padEnd(26)],
        datasets: [{
          label: ' % ',
          backgroundColor: ['#48C78E', '#F14668'],
          data: [upTime, 100.0 - upTime]
        }],
      },
      options: { plugins: { legend: { position: 'right', maxWidth: 135 }}}
    };
  }

  function queryActivity() {
    processing = true;
    const [instance, atrange] = [query.criteria.instance().identity(), query.criteria.atrange()];
    Promise.all([queryInstance(instance),
                 queryLastEvent(instance, atrange.atfrom),
                 queryEvents(instance, atrange.atfrom, atrange.atto)])
      .then(function(data) {
        results = {};
        [results.instances, results.lastevent, results.events] = data;
        activity = extractActivity(results);
      })
      .finally(function() { processing = false; });
  }

  query.onExecute('InstanceActivity', queryActivity);

  onMount(function() {
    tick().then(queryActivity);
  });

  onDestroy(function() {
    objectUrls.cleanup();
  });
</script>


{#if processing}
  <div class="content">
    <p><SpinnerIcon /> Loading Instance Activity...</p>
  </div>
{:else if activity}
  <div class="columns">
    <div class="column is-2">
      <p class="has-text-weight-bold">
        {activity.results.length > 1 ? 'Instances' : 'Instance'}
      </p>
    </div>
    <div class="column is-10">
      <p>
        <a href={'#'} on:click|preventDefault={function() { objectUrls.openObject(results); }}>
          results <i class="fa fa-up-right-from-square"></i></a>&nbsp;
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
      <p><i class="fa fa-triangle-exclamation fa-lg ml-3 mr-1"></i> No instance activity found</p>
    </div>
  {:else}
    {#each activity.results as entry}
      <div class="columns">
        <div class="column mt-0 pt-0">
          <table class="table is-thinner"><tbody>
            <tr><td class="label-column"></td><td></td><tr>
            <tr><td class="label-column has-text-weight-bold"
                    title="Name of the instance">Name</td>
              <td class="notranslate">{entry.instance}</td></tr>
            <tr><td class="label-column has-text-weight-bold"
                    title="Date and time the instance was created">Created</td>
              <td class="notranslate">{shortISODateTimeString(entry.created)}</td></tr>
            <tr><td class="label-column has-text-weight-bold"
                    title="Reporting period, starting at 'created' or 'from' date, whichever is latest">Range</td>
              <td class="notranslate">{humanDuration(entry.range)}</td></tr>
            <tr><td class="label-column has-text-weight-bold"
                    title="Total uptime of the instance">Uptime</td>
              <td class="notranslate">{humanDuration(entry.uptime)}</td></tr>
            <tr><td class="label-column has-text-weight-bold"
                    title="Uptime as percentage of range (reporting period)">Available</td>
              <td class="notranslate">{floatToPercent(entry.available)}</td></tr>
            <tr><td class="label-column has-text-weight-bold"
                    title="Number of times the instance was running">Sessions</td>
              <td class="notranslate">{entry.sessions}</td></tr>
          </tbody></table>
        </div>
        <div class="column">
          {#if !processing}
            <div class="chart"><ChartCanvas data={chartData(entry)} /></div>
          {/if}
        </div>
      </div>
    {/each}
  {/if}
{/if}


<style>
  .chart {
    max-width: 330px;
    margin: -70px auto -60px auto;
  }

  .label-column {
    width: 40%;
    min-width: 90px;
  }
</style>
