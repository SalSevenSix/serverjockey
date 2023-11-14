<script>
  import { onMount } from 'svelte';
  import { newGetRequest } from '$lib/sjgmsapi';

  let loaded = false;
  let hasServerLink = false;

  onMount(function() {
    fetch('/instances/serverlink', newGetRequest())
      .then(function(response) { hasServerLink = response.ok; })
      .finally(function() { loaded = true; });
  });
</script>


{#if loaded}
  {#if hasServerLink}
    <slot />
  {:else}
    <slot name="placeholder" />
  {/if}
{/if}
