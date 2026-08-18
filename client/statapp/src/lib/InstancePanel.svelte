<script>
  import { onMount } from 'svelte';
  import { resolve } from '$app/paths';
  import { fetchJson } from '$lib/util';
  import { extractActivity as extractInstance } from 'common/activity/instance';
  import { extractActivity as extractPlayer } from 'common/activity/player';
  import MessageBanner from '$lib/MessageBanner.svelte';
  import InstanceTitle from '$lib/InstanceTitle.svelte';
  import InstanceStatus from '$lib/InstanceStatus.svelte';
  import InstanceSummary from '$lib/InstanceSummary.svelte';
  import PlayerSummary from '$lib/PlayerSummary.svelte';
  import PlayerTop from '$lib/PlayerTop.svelte';
  import PlayerChart from '$lib/PlayerChart.svelte';
  import PlayerOnline from '$lib/PlayerOnline.svelte';

  let { instance } = $props();
  let data = $state(null);

  function buildUrl(file) {
    return resolve('/data/' + instance + '-' + file);
  }

  onMount(function() {
    Promise.all([
      fetchJson(buildUrl('instance-status.json')),
      fetchJson(buildUrl('player-online.json')),
      fetchJson(buildUrl('instances.json')),
      fetchJson(buildUrl('instance-lastevent.json')),
      fetchJson(buildUrl('instance-events.json')),
      fetchJson(buildUrl('player-lastevent.json')),
      fetchJson(buildUrl('player-events.json'))
    ]).then(function(fetched) {
      const [res, ires, pres] = [{}, {}, {}];
      res.s = fetched[0];
      res.o = fetched[1];
      [ires.instances, ires.lastevent, ires.events] = fetched.slice(2, 5);
      res.s.module = ires.instances.records ? ires.instances.records[0][2] : '';
      res.i = extractInstance(ires);
      res.i.results = res.i.results[0];
      [pres.lastevent, pres.events] = fetched.slice(5);
      res.p = extractPlayer(pres);
      res.p.results = Object.values(res.p.results)[0];
      data = res;
    });
  });
</script>


{#if data}
  <InstanceTitle {data} />
  <InstanceStatus {data} />
  <InstanceSummary {data} />
  <PlayerOnline {data} />
  {#if data.p.results}
    <PlayerSummary {data} />
    <PlayerChart {data} />
    <PlayerTop {data} />
  {:else}
    <MessageBanner text="No Player History Found" />
  {/if}
  <div class="footpad"></div>
{/if}


<style>
  .footpad {
    height: 1.2em;
  }
</style>
