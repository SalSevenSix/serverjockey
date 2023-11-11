<script>
  import { onMount } from 'svelte';
  import { newGetRequest } from '$lib/sjgmsapi';

  let hasStore = false;

  onMount(function() {
    fetch('/store', newGetRequest())
      .then(function(response) { hasStore = response.ok; });
  });
</script>


{#if hasStore}
  <slot />
{/if}
