<script>
  import { onMount } from 'svelte';
  import { shortISODateTimeString, humanDuration } from 'common/util/util';
  import { fetchJson } from '$lib/util';
  import InstancePanel from '$lib/InstancePanel.svelte';

  let meta = $state(null);

  onMount(function() {
    fetchJson('/data/meta.json').then(function(data) { meta = data; });
  });
</script>


{#if meta}
  {#each meta.instances as instance}
    <InstancePanel {instance} />
  {/each}
  <div class="dashpanel font-monospace text-align-center"><p>
    updated {shortISODateTimeString(meta.updated)}<br>
    [&nbsp;{humanDuration(Date.now() - meta.updated, 'ms')} ago&nbsp;]</p>
  </div>
{/if}
