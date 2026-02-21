<script>
  import { scrollto } from 'svelte-scrollto-next';
  import { surl } from '$lib/util/sjgmsapi';
  import ExtLink from '$lib/widget/ExtLink.svelte';
  import CodeBlock from '$lib/widget/CodeBlock.svelte';
  import WebappTitle from '$lib/guides/common/WebappTitle.svelte';
  import WebappServerInstall from '$lib/guides/common/WebappServerInstall.svelte';
  import WebappConfigRun from '$lib/guides/common/WebappConfigRun.svelte';
  import WebappGenerateConfig from '$lib/guides/common/WebappGenerateConfig.svelte';
  import WebappAdditionalInformation from '$lib/guides/common/WebappAdditionalInformation.svelte';
  import WebappPortForward from '$lib/guides/common/WebappPortForward.svelte';
</script>


<WebappTitle module="hytale" serverName="Hytale">
  <p>
    <ExtLink href="https://hytale.com" notranslate>Hytale</ExtLink>
    is a voxel based open sandbox game heavily inspired by Minecraft, but with a bigger focus on RPG style adventure.
    This guide will show you how to install, configure and run a Hytale server using this Webapp.
  </p>
  <p>
    Go to the <a href="#additionalInformation" use:scrollto={'#additionalInformation'}>additional information</a>
    section at the end for help on;
  </p>
  <ul>
    <li><a href="#portForwarding" use:scrollto={'#portForwarding'}>Port Forwarding</a></li>
    <li><a href="#serverUpdates" use:scrollto={'#serverUpdates'}>Checking for Server Updates</a></li>
    <li><a href="#autoModDownloads" use:scrollto={'#autoModDownloads'}>Automatic Mod Downloads</a></li>
  </ul>
</WebappTitle>
<WebappServerInstall module="hytale" />
<WebappGenerateConfig />
<WebappConfigRun />
<WebappAdditionalInformation />
<WebappPortForward serverName="Hytale" configName="Command Line Args"
  portsList={[{ purpose: 'Server', port: 5520, protocal: 'UDP' }]}>
&quot;_comment_server_upnp&quot;: &quot;Try to automatically redirect server port on home network using UPnP&quot;,
&quot;server_upnp&quot;: false
</WebappPortForward>

<div class="content pt-4" id="serverUpdates">
  <h4 class="title is-5">Checking for Server Updates</h4>
  <p>
    ServerJockey has some features to help keep your Hytale server up-to-date on the latest version.
    When the server is started, it will automatically check to see if a new version is available by console command.
    Another check is done every 6 hours. If a newer version is found, the server status in both
    the webapp and in discord will show a notice like follows;
  </p>
  <p class="is-family-monospace">
    &nbsp;&nbsp;&nbsp;<span class="has-text-weight-bold">Notice</span>
    &nbsp;Server Update Required
  </p>
  <p>
    The checking frequency can be changed in the
    <span class="has-text-weight-bold">Command Line Args</span>
    configuration. Specify the frequency in minutes.
    Default is 360 minutes (6 hours), use 0 to disable checks.
  </p>
  <CodeBlock nocopy>
&quot;_comment_check_update_minutes&quot;: &quot;Check for server updates frequency, use zero to disable&quot;,
&quot;check_update_minutes&quot;: 360</CodeBlock>
  <p>
    In addition to automated update checks. The
    <a href={surl('/guides/cli')}>Serverjockey CLI</a>
    has a command that can be used to check if the server requires an update.
    The example CLI command sequence below shows how it can be used to check and update the server if needed.
  </p>
  <ol>
    <li>Select the instance called  <span class="is-family-monospace notranslate">mytale</span></li>
    <li>If the server is not running, then stop processing commands and exit</li>
    <li>If the server version is the latest, then stop processing commands and exit</li>
    <li>Stop the server then wait 10 seconds for that to happen</li>
    <li>Backup both the game world save and the installed server</li>
    <li>Install the latest version of the server</li>
    <li>Start up the server</li>
  </ol>
  <CodeBlock>
serverjockey_cmd.pyz -c \
  use:mytale exit-down exit-no-update \
  server:stop sleep:10 \
  backup-world backup-runtime \
  install-runtime server:start</CodeBlock>
</div>

<div class="content pt-4" id="autoModDownloads">
  <h4 class="title is-5">Automatic Mod Downloads</h4>
  <p>
    ServerJockey provides a way to manually upload and manage Hytale plugins &amp; mods in the
    <span class="has-text-weight-bold">Mod Files</span>
    section on the webapp. In addition to this, there is an
    <span class="has-text-weight-bold">Auto Download Mods</span>
    cofiguration file in this section. It can be used to automatically download mods and update them
    as needed when the server is started. Currently only the
    <ExtLink href="https://modtale.net" notranslate>Modtale</ExtLink>
    mod hosting service is supported.
  </p>
  <p>
    Add mods by
    <span class="has-text-weight-bold">Project ID</span>
    into the
    <span class="is-family-monospace">mods</span>
    list. The Project ID that includes the mod name in the URL is also acceptable.
    Use
    <span class="is-family-monospace">enable</span>
    to turn off or on automatic updates.
    Use
    <span class="is-family-monospace">ignoreServerVersion</span>
    to only download mods compatible with your server version (false),
    or always get the latest mod version regardless (true).
  </p>
  <p>
    The example below will automatically download three mods and keep them up-to-date.
  </p>
  <CodeBlock nocopy>&#123;
  &quot;enabled&quot;: true,
  &quot;ignoreServerVersion&quot;: true,
  &quot;services&quot;: [
    &#123;
      &quot;type&quot;: &quot;modtale-v1&quot;,
      &quot;endpoint&quot;: &quot;https://api.modtale.net&quot;,
      &quot;mods&quot;: [
        &quot;better-repair-kits-1efe3615-9919-45e2-8484-d4a31f7c5260&quot;,
        &quot;torches-657746f9-6c0e-4c2b-9070-939d0bfbf1f0&quot;,
        &quot;dd7cba43-5dfa-4b27-84d3-0ed78f2f9a45&quot;
      ]
    &#125;
  ]
&#125;</CodeBlock>
</div>
