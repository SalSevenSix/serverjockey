<script>
  import { onMount, onDestroy, getContext } from 'svelte';
  import { queryEvents, queryLastEvent, extractActivity } from '$lib/PlayerActivity';
  import { floatToPercent, humanDuration, shortISODateTimeString } from '$lib/util';
  import SpinnerIcon from '$lib/SpinnerIcon.svelte';
  import ChartCanvas from '$lib/ChartCanvas.svelte';

  const instance = getContext('instance');

  let objectUrls = [];
  let eventResults = null;
  let lastEventResults = null;
  let activity = null;

  $: if (eventResults && lastEventResults) { onResults(); }
  function onResults() {
    activity = extractActivity(eventResults, lastEventResults);
  }

  function showResults() {
    if (!activity) return;
    let results = { lastevent: lastEventResults, events: eventResults };
    let blob = new Blob([JSON.stringify(results)], { type : 'text/plain;charset=utf-8' });
    let objectUrl = window.URL.createObjectURL(blob);
    objectUrls.push(objectUrl);
    window.open(objectUrl).focus();
  }

  function queryActivity(criteria) {
    activity = null;
    eventResults = null;
    lastEventResults = null;
    queryEvents(criteria).then(function(results) { eventResults = results; });
    queryLastEvent(criteria).then(function(results) { lastEventResults = results; });
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
      <div class="column is-one-fifth mb-0 pb-0">
        <p class="has-text-weight-bold">Players</p>
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
    <!-- each player -->
  </div>
{:else}
  <div class="content">
    <p><SpinnerIcon /> Loading Player Activity...<br /><br /></p>
  </div>
{/if}
