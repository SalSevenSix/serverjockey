<script>
  import CheckServerLink from '$lib/CheckServerLink.svelte';
  import DiscordBotSetupGuide from './DiscordBotSetupGuide.svelte';
  import DiscordBotPlaceholder from './DiscordBotPlaceholder.svelte';
</script>


<CheckServerLink>
  <DiscordBotSetupGuide />
  <DiscordBotPlaceholder slot="placeholder" />
</CheckServerLink>
