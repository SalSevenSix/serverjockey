<script>
  import { onMount } from 'svelte';
  import { newGetRequest } from '$lib/util/sjgmsapi';

  let loaded = false;
  let hasServerLink = false;
  let hasToken = false;

  onMount(function() {
    fetch('/instances/serverlink/config', newGetRequest())
      .then(function(response) {
        if (!response.ok) return null;
        return response.json();
      })
      .then(function(json) {
        if (!json) return;
        hasServerLink = true;
        if (json.BOT_TOKEN) { hasToken = true; }
      })
      .finally(function() {
        loaded = true;
      });
  });
</script>


{#if loaded}
  {#if hasServerLink}
    <slot {hasToken} />
  {:else}
    <slot name="placeholder" />
  {/if}
{:else}
  <slot name="loading" />
{/if}
