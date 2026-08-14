<script>
  import { onMount } from 'svelte';
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
{/if}
