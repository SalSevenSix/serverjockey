<script>
  import { onMount } from 'svelte';
  import { goto } from '$app/navigation';
  import { instance } from '$lib/serverjockeyapi';
  import ServerStatusStore from '$lib/ServerStatusStore.svelte';

  onMount(function() {
    if (!$instance.identity) return goto('/servers');
  });
</script>


{#if $instance.identity}
  <div class="columns is-centered">
    <div class="column is-half">
      <h1 class="title is-3">{$instance.identity} | {$instance.module}</h1>
    </div>
  </div>
  <ServerStatusStore>
    <slot />
  </ServerStatusStore>
{:else}
  <div class="block">
    <p>No instance set</p>
  </div>
{/if}
