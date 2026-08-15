<script>
  import { onMount } from 'svelte';
  import { fetchJson } from '$lib/util';
  import { extractActivity as extractInstance } from 'common/activity/instance';
  import { extractActivity as extractPlayer } from 'common/activity/player';
  import InstanceTitle from '$lib/InstanceTitle.svelte';
  import InstanceStatus from '$lib/InstanceStatus.svelte';
  import InstanceSummary from '$lib/InstanceSummary.svelte';
  import PlayerSummary from '$lib/PlayerSummary.svelte';
  import PlayerTop from '$lib/PlayerTop.svelte';
  import PlayerChart from '$lib/PlayerChart.svelte';
  import PlayerOnline from '$lib/PlayerOnline.svelte';

  let { instance } = $props();
  let data = $state(null);

  onMount(function() {
    Promise.all([
      fetchJson('/data/' + instance + '-instance-status.json'),
      fetchJson('/data/' + instance + '-player-online.json'),
      fetchJson('/data/' + instance + '-instances.json'),
      fetchJson('/data/' + instance + '-instance-lastevent.json'),
      fetchJson('/data/' + instance + '-instance-events.json'),
      fetchJson('/data/' + instance + '-player-lastevent.json'),
      fetchJson('/data/' + instance + '-player-events.json')
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
  <PlayerSummary {data} />
  <PlayerChart {data} />
  <PlayerTop {data} />
{/if}
