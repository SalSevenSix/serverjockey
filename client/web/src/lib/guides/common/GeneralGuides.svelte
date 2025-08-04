<script>
  import { browserName } from '$lib/util/browserutil';
  import { surl } from '$lib/util/sjgmsapi';
  import ExtLink from '$lib/widget/ExtLink.svelte';

  const isChrome = browserName === 'Chrome';
  const isEdge = browserName === 'Edge';
</script>


<div class="columns">
  <div class="column is-one-fifth pb-0 has-text-weight-bold">
    <a id="generalGuidesDiscordBotSetup"
       href={surl('/guides/discord/setup')}><i class="fa-brands fa-discord fa-lg theme-black-white"></i>&nbsp;
      Discord Bot Setup</a>
  </div>
  <div class="column is-four-fifths content">
    <p>
      This guide will show you how to setup the Discord bot which can be used to manage your servers as an
      alternative to this webapp. The instructions are detailed. If you are unfamiliar with Discord, the guide
      includes instructions on how to register a new Discord account and create a new Discord server if needed.
    </p>
  </div>
</div>

<div class="columns">
  <div class="column is-one-fifth pb-0 has-text-weight-bold">
    <a id="generalGuidesDiscordBotUsage"
       href={surl('/guides/discord/usage')}><i class="fa-brands fa-discord fa-lg theme-black-white"></i>&nbsp;
      Discord Bot Usage</a>
  </div>
  <div class="column is-four-fifths content">
    <p>
      This guide will show you how to use the Discord bot to create, configure and start
      a Project Zomboid server as an example. The same process can be used on other supported
      game servers too. Please ensure the bot is setup and working first!
    </p>
  </div>
</div>

<div class="columns">
  <div class="column is-one-fifth pb-0 has-text-weight-bold">
    <a id="generalGuidesBrowserExtension"
       href={surl('/guides/extension')}><i class="fa-brands {isEdge ? 'fa-edge' : 'fa-chrome'} fa-lg theme-black-white"></i>
      Browser Extension</a>
  </div>
  <div class="column is-four-fifths content">
    <p>
      ServerJockey has a
      {#if isChrome}
        <ExtLink href="https://chromewebstore.google.com/detail/serverjockey/bcgjnafdidbpegbeijnbpaioipfckiaj"
           >browser extension</ExtLink>
        for Google Chrome
      {:else if isEdge}
        <ExtLink href="https://microsoftedge.microsoft.com/addons/detail/serverjockey/fcfknahceaoeohgehmbialifgdbihloe"
           >browser extension</ExtLink>
        for Microsoft Edge
      {:else}
        browser extension for Google Chrome and Microsoft Edge
      {/if}
      that can be used to manage mods for Project Zomboid servers.
      It allows you to add and remove mods using Steam Workshop pages.
    </p>
  </div>
</div>

<div class="columns">
  <div class="column is-one-fifth pb-0 has-text-weight-bold notranslate">
    <a id="generalGuidesVirtualBox"
       href={surl('/guides/virtualbox')}><i class="fa fa-computer fa-lg theme-black-white"></i>&nbsp;
      VirtualBox</a>
  </div>
  <div class="column is-four-fifths content">
    <p>
      ServerJockey is available pre-installed as a VirtualBox Appliance. If you are using this option,
      this guide provides information on how to configure, use and care for the appliance.
    </p>
  </div>
</div>


<style>
  .fa, .fa-brands {
    width: 1.15em;
  }
</style>
