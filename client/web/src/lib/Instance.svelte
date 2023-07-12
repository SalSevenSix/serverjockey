<script>
  import { onMount } from 'svelte';
  import { goto } from '$app/navigation';
  import { instance } from '$lib/instancestores';
  import ServerStatusStore from '$lib/ServerStatusStore.svelte';

  onMount(function() {
    if (!$instance.identity) { goto('/servers'); }
  });
</script>


{#if $instance.identity}
  <div class="columns is-centered">
    <div class="column is-three-quarters">
      <h1 class="title is-3">{$instance.identity} &nbsp;<i class="fa fa-cube"></i>&nbsp; {$instance.module}</h1>
    </div>
  </div>
  <ServerStatusStore>
    <slot />
  </ServerStatusStore>
{:else}
  <div class="content">
    <p>No instance set</p>
  </div>
{/if}
