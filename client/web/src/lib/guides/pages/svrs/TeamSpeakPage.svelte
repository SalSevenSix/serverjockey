<script>
  import ExtLink from '$lib/widget/ExtLink.svelte';
  import WebappTitle from '$lib/guides/common/WebappTitle.svelte';
  import WebappServerInstall from '$lib/guides/common/WebappServerInstall.svelte';
  import WebappConfigRun from '$lib/guides/common/WebappConfigRun.svelte';
</script>


<WebappTitle module="teamspeak" serverName="TeamSpeak">
  <p>
    <ExtLink href="https://www.teamspeak.com" notranslate>TeamSpeak</ExtLink>
    is a high quality Voice Chat server with other features. It provides a private self-hosted alternative to Discord.
    This guide will show you how to install, configure and run a TeamSpeak server using this Webapp.
  </p>
</WebappTitle>
<WebappServerInstall module="teamspeak" />
<WebappConfigRun />
