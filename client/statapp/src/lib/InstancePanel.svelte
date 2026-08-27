<script>
  import { onMount } from 'svelte';
  import { durl, fetchJson, fetchOk } from '$lib/util';
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
    return durl('/' + instance + '-' + file);
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
    ]).then(function([status, online, irecord, ilastevent, ievents, plastevent, pevents]) {
      const out = { s: status, o: online, i: null, p: null };
      out.s.module = irecord.records ? irecord.records[0][2] : 'unknown';
      if (fetchOk(ilastevent) && fetchOk(ievents)) {
        out.i = extractInstance({ instances: irecord, lastevent: ilastevent, events: ievents });
        out.i.results = out.i.results[0];
      }
      if (fetchOk(plastevent) && fetchOk(pevents)) {
        out.p = extractPlayer({ lastevent: plastevent, events: pevents });
        out.p.results = Object.values(out.p.results)[0];
      }
      data = out;
    });
  });
</script>


{#if data}
  <InstanceTitle {data} />
  <InstanceStatus {data} />
  {#if data.i}
    <InstanceSummary {data} />
  {:else}
    <MessageBanner text="No Server History Found" />
  {/if}
  <PlayerOnline {data} />
  {#if data.p && data.p.results}
    <PlayerSummary {data} />
    <PlayerChart {data} />
    <PlayerTop {data} />
  {:else}
    <MessageBanner text="No Player History Found" />
  {/if}
  <div class="footpad"></div>
{/if}
