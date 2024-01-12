<script>
  import SpinnerIcon from '$lib/widget/SpinnerIcon.svelte';
  import CheckServerLink from '$lib/svrlink/CheckServerLink.svelte';
  import DiscordBotSetupGuide from './DiscordBotSetupGuide.svelte';
  import DiscordBotPlaceholder from './DiscordBotPlaceholder.svelte';
</script>


<CheckServerLink>
  <DiscordBotSetupGuide />
  <DiscordBotPlaceholder slot="placeholder" />
  <div class="content" slot="loading">
    <p><SpinnerIcon /> loading...</p>
  </div>
</CheckServerLink>
