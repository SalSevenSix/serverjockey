<script>
  import { onMount } from 'svelte';
  import { durl, fetchJson, fetchOk } from '$lib/util';
  import MessageBanner from '$lib/MessageBanner.svelte';
  import InstancePanel from '$lib/InstancePanel.svelte';
  import Timestamp from '$lib/Timestamp.svelte';

  let meta = $state(null);

  onMount(function() {
    fetchJson(durl('/meta.json')).then(function(data) { meta = data; });
  });
</script>


{#if meta}
  {#if fetchOk(meta)}
    {#each meta.instances as instance}
      <InstancePanel {instance} />
    {/each}
    <Timestamp {meta} />
  {:else}
    <MessageBanner text="No Data Found :(" />
  {/if}
{/if}
