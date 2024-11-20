<script>
  import { browserName } from '$lib/util/util';
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

<div class="columns">
  <div class="column is-one-fifth pb-0 has-text-weight-bold">
    <a id="generalGuidesCommandLineInterface"
       href={surl('/guides/cli')}><i class="fa fa-terminal fa-lg theme-black-white"></i>
      Command Line Interface</a>
  </div>
  <div class="column is-four-fifths content">
    <p>
      ServerJockey has a Command Line Interface (CLI), which is useful for automating server management.
      This guide will show how to control servers and perform administrative tasks using the CLI.
    </p>
  </div>
</div>

<div class="columns">
  <div class="column is-one-fifth pb-0 has-text-weight-bold">
    <a id="generalGuidesGameSaveMigrations"
       href={surl('/guides/migrations')}><i class="fa fa-dolly fa-lg theme-black-white"></i>
      Game Save Migrations</a>
  </div>
  <div class="column is-four-fifths content">
    <p>
      This guide will show you how to migrate an existing game save (world) into ServerJockey.
      Also how a game save can be copied or moved between ServerJockey instances, on the same or different machine.
    </p>
  </div>
</div>

<div class="columns">
  <div class="column is-one-fifth pb-0 has-text-weight-bold">
    <a id="generalGuidesHostingBehindNginx"
       href={surl('/guides/nginx')}><i class="fa fa-server fa-lg theme-black-white"></i>
      Hosting behind Nginx</a>
  </div>
  <div class="column is-four-fifths content">
    <p>
      Nginx is a popular web server with a powerful reverse proxy feature.
      This guide will show how to combine Nginx and ServerJockey to create a more professional hosting setup.
    </p>
  </div>
</div>

<div class="columns">
  <div class="column is-one-fifth pb-0 has-text-weight-bold">
    <a id="generalGuidesMonitoringWithPrometheus"
       href={surl('/guides/prometheus')}><i class="fa fa-wave-square fa-lg theme-black-white"></i>&nbsp;
      Monitoring with Prometheus</a>
  </div>
  <div class="column is-four-fifths content">
    <p>
      Prometheus is a flexible open-source monitoring system that stores metrics in an efficient time series database.
      It can be used to monitor machine health and game servers managed by ServerJockey.
      This guide will show how to install and configure Prometheus.
    </p>
  </div>
</div>

<div class="columns">
  <div class="column is-one-fifth pb-0 has-text-weight-bold">
    <a id="generalGuidesReportingWithGrafana"
       href={surl('/guides/grafana')}><i class="fa fa-chart-line fa-lg theme-black-white"></i>
      Reporting with Grafana</a>
  </div>
  <div class="column is-four-fifths content">
    <p>
      Grafana is an observability platform that provides graphs and alerts from metrics data sources such as Prometheus.
      This guide will show how to install, configure and integrate Grafana with Prometheus.
    </p>
  </div>
</div>

<div class="columns">
  <div class="column is-one-fifth pb-0 has-text-weight-bold">
    <a id="generalGuidesOffsiteBackupsUsingMEGA"
       href={surl('/guides/megasync')}><i class="fa fa-boxes-packing fa-lg theme-black-white"></i>&nbsp;
      Offsite backups using MEGA</a>
  </div>
  <div class="column is-four-fifths content">
    <p>
      MEGA is a popular cloud storage service with a generous free-tier plan.
      This guide will show you how to install and configure the MEGA CMD App
      to automatically copy backups to the MEGA platform for off-site backups.
    </p>
  </div>
</div>


<style>
  .fa, .fa-brands {
    width: 1.2em;
  }
</style>
