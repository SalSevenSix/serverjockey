<script>
  import SpinnerIcon from '$lib/widget/SpinnerIcon.svelte';
  import CheckServerLink from '$lib/svrlink/CheckServerLink.svelte';
  import ServerStatusStore from '$lib/instance/ServerStatusStore.svelte';
  import DiscordSetupPage from '$lib/guides/pages/DiscordSetupPage.svelte';
</script>


<CheckServerLink>
  <ServerStatusStore identity="serverlink">
    <DiscordSetupPage />
  </ServerStatusStore>

  <div class="columns mb-5 pb-6" slot="placeholder">
    <div class="column is-one-quarter content">
      <p class="has-text-centered">
        <i class="fa fa-triangle-exclamation fa-10x"></i>
      </p>
    </div>
    <div class="column is-three-quarters content">
      <h2 class="title is-3 mt-2">Guide Unavailable</h2>
      <p>
        The ServerLink discord bot does not appear to be installed on this system.
        Therefore it is not possible to setup the bot.
      </p>
    </div>
  </div>

  <div class="content" slot="loading">
    <p><SpinnerIcon /> loading...</p>
  </div>
</CheckServerLink>
