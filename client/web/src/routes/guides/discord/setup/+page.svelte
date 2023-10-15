<script>
  import { onMount } from 'svelte';
  import { newGetRequest } from '$lib/sjgmsapi';
  import DiscordBotSetupGuide from './DiscordBotSetupGuide.svelte';

  let loaded = false;
  let showGuide = false;

  onMount(function() {
    fetch('/instances/serverlink', newGetRequest())
      .then(function(response) { showGuide = response.ok; })
      .finally(function() { loaded = true; });
  });
</script>


{#if loaded}
  {#if showGuide}
    <DiscordBotSetupGuide />
  {:else}
    <div class="columns">
      <div class="column is-one-quarter content">
        <p class="has-text-centered">
          <i class="fa fa-triangle-exclamation fa-10x"></i>
        </p>
      </div>
      <div class="column is-three-quarters content">
        <h2 class="title is-3 mt-2">Guide Unavailable</h2>
        <p>
          The ServerLink discord bot program does not appear to be installed on this system.
          Therefore it is not possible to setup the bot.
        </p>
        <p>
          <br /><br /><br /><br /><br /><br />
          <br /><br /><br /><br /><br />
        </p>
      </div>
    </div>
  {/if}
{:else}
  <div class="content">
    <p>
      <br /><br /><br /><br /><br />
      <br /><br /><br /><br /><br />
      <br /><br /><br /><br /><br />
    </p>
  </div>
{/if}
