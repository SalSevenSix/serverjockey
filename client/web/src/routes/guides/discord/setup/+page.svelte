<script>
  import CheckServerLink from '$lib/CheckServerLink.svelte';
  import DiscordBotSetupGuide from './DiscordBotSetupGuide.svelte';
  import DiscordBotPlaceholder from './DiscordBotPlaceholder.svelte';
  import SpinnerIcon from '$lib/SpinnerIcon.svelte';
</script>


<CheckServerLink>
  <DiscordBotSetupGuide />
  <DiscordBotPlaceholder slot="placeholder" />
  <div class="content" slot="loading">
    <p><SpinnerIcon /> loading...</p>
  </div>
</CheckServerLink>
