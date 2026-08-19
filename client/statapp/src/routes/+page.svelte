<script>
  import { onMount } from 'svelte';
  import { resolve } from '$app/paths';
  import { fetchJson } from '$lib/util';
  import MessageBanner from '$lib/MessageBanner.svelte';
  import InstancePanel from '$lib/InstancePanel.svelte';
  import Timestamp from '$lib/Timestamp.svelte';

  let meta = $state(null);

  onMount(function() {
    fetchJson(resolve('/data/meta.json')).then(function(data) { meta = data; });
  });
</script>


{#if meta}
  {#if meta instanceof Error}
    <MessageBanner text="No Data Found :(" />
  {:else}
    {#each meta.instances as instance}
      <InstancePanel {instance} />
    {/each}
    <Timestamp {meta} />
  {/if}
{/if}
