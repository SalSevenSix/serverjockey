<script>
  import { scrollto } from 'svelte-scrollto-element';
  import BackToTop from '$lib/BackToTop.svelte';
</script>

<div class="columns">
  <div class="column is-one-quarter">
    <figure class="image pt-3"><img src="/assets/icons/pz_icon.jpg" alt="Project Zomboid icon" /></figure>
  </div>
  <div class="column content">
    <h2 class="title is-3 mt-2">Project Zomboid</h2>
    <p>
      <a href="https://projectzomboid.com" target="_blank">
        Project Zomboid <i class="fa fa-up-right-from-square"></i></a>
      is a zombie apocalypse survival horror game with crafting &amp; RPG elements and a focus on realism.
      ServerJockey provides full support for multiplayer servers on both the webapp and discord.
    </p>
    <p>
      This guide covers installing, configuring and starting a Project Zomboid server using Discord.
      You will need to <a href="/guides/discord">setup the discord bot</a> first if you have not already.
      When ready, <a href="#setupWithBotOne" use:scrollto={'#setupWithBotOne'}>jump to the first step</a> to begin.
    </p>
    <p>
      Go to the <a href="#additionalInformation" use:scrollto={'#additionalInformation'}>additional information</a>
      section at the end for help on;
    </p>
    <ul>
      <li><a href="#configurationFiles" use:scrollto={'#configurationFiles'}>Configuration Files</a></li>
      <li><a href="#portForwarding" use:scrollto={'#portForwarding'}>Port Forwarding</a></li>
      <li><a href="#memoryAllocation" use:scrollto={'#memoryAllocation'}>Memory Allocation</a></li>
    </ul>
  </div>
</div>

<div class="content" id="setupWithBotOne">
  <hr />
  <h3 class="title is-4">Server setup using the Discord bot</h3>
</div>

<div class="content">
  <p><span class="step-title"></span>
    First step is to create an instance for the Project Zomboid server. If you are following this guide after the
    <a href="/guides/discord">discord bot setup guide</a>, then the instance already exists, so you can
    <a href="#setupWithBotTwo" use:scrollto={'#setupWithBotTwo'}>jump to the next step</a>.
  </p>
  <p>
    For this guide the instance is called <span class="has-text-weight-bold">myserver</span>. You can give your
    instance a different name, but it must be lower case characters and numbers only, no spaces or special characters.
    The second command value is <span class="has-text-weight-bold">projectzomboid</span>. This is the type of instance.
  </p>
  <p>
    Enter the command in discord as shown below to create the instance.
  </p>
  <pre class="pre is-thinner">!create myserver projectzomboid</pre>
  <figure><img src="/assets/setup/38_create_instance_success.png" alt="Create Instances Success" /></figure>
</div>

<div class="content" id="setupWithBotTwo">
  <p><span class="step-title"></span>
    Now enter the help command. Now that there is an instance, you will see all the commands for that type of instance.
  </p>
  <pre class="pre is-thinner">!help</pre>
  <figure><img src="/assets/setup/39_help_pz.png" alt="Help PZ" loading="lazy" /></figure>
</div>

<div class="content">
  <p><span class="step-title"></span>
    Although the instance has been created, the Project Zomboid server itself is not installed yet.
    The stable version can now be downloaded and installed with the command shown below. The bot reacts
    with an hourglass emoji initially as the process happens. Once complete, the hourglass will be replaced
    with a green tick. Also the log output from SteamCMD will be attached. You can check this to ensure
    the server was installed without issue.
  </p>
  <pre class="pre is-thinner">!deployment install-runtime</pre>
  <figure>
    <img src="/assets/setup/40_deploy_runtime_hourglass.png" alt="Deploy Runtime Hourglass" loading="lazy" />
  </figure>
  <figure>
    <img src="/assets/setup/40_deploy_runtime_success.png" alt="Deploy Runtime Success" loading="lazy" />
  </figure>
</div>

<div class="content">
  <p><span class="step-title"></span>
    With the server installed, it can now be started with the following command. Same as the server install,
    an hourglass emoji is shown then replaced with a green tick when the server has fully started.
  </p>
  <pre class="pre is-thinner">!server start</pre>
  <figure><img src="/assets/setup/41_server_start_hourglass.png" alt="Start Server Hourglass" loading="lazy" /></figure>
  <figure><img src="/assets/setup/41_server_start_success.png" alt="Start Server Success" loading="lazy" /></figure>
</div>

<div class="content">
  <p><span class="step-title"></span>
    You can check the status of the server at any time with the following command.
    Now that the server is up, the server version and connection details are shown.
  </p>
  <pre class="pre is-thinner">!server</pre>
  <figure><img src="/assets/setup/42_server_status_up.png" alt="Server Status Up" loading="lazy" /></figure>
</div>

<div class="content">
  <p><span class="step-title"></span>
    Before we continue to login and play, the server configuration needs attention. After starting the
    Project Zomboid server for the first time, the configuration files are created with default values.
    So stop the server with the following command.
  </p>
  <pre class="pre is-thinner">!server stop</pre>
  <figure><img src="/assets/setup/43_server_stop.png" alt="Server Stop" loading="lazy" /></figure>
</div>

<div class="content">
  <p><span class="step-title"></span>
    The server INI file can be downloaded as an attachment with the following command.
    See the server command list for other configuration files that can be downloaded.
    Save this file to disk somewhere to edit it.
  </p>
  <pre class="pre is-thinner">!getconfig ini</pre>
  <figure><img src="/assets/setup/44_getconfig_ini.png" alt="Get Config INI" loading="lazy" /></figure>
</div>

<div class="content">
  <p><span class="step-title"></span>
    For the purpose of this guide. I have only updated a the public server name and welcome message
    in the downloaded INI file. Typically you will make more changes. You can look at the
    <a href="#additionalInformation" use:scrollto={'#additionalInformation'}>additional information</a>
    at the end of this guide for more help on Project Zomboid server configuration.
  </p>
  <pre class="pre is-thinner">PublicName=ZomBox demo server
ServerWelcomeMessage=Welcome to the ZomBox demo server.</pre>
</div>

<div class="content">
  <p><span class="step-title"></span>
    After making changes to the downloaded INI file. You can now upload it back to the server.
    Attach the INI file in Discord to upload it with the following command.
    Once again, the bot will react with a green tick emoji to show that the command was successful.
  </p>
  <pre class="pre is-thinner">!setconfig ini</pre>
  <figure><img src="/assets/setup/46_setconfig_ini.png" alt="Set Config INI" loading="lazy" /></figure>
</div>

<div class="content">
  <p><span class="step-title"></span>
    The server configuration has now been updated. However the server created a game world (map files)
    using the default configuration. You can delete the world with the following command.
  </p>
  <pre class="pre is-thinner">!deployment wipe-world-save</pre>
  <figure><img src="/assets/setup/47_wipe_map.png" alt="Wipe Map" loading="lazy" /></figure>
</div>

<div class="content">
  <p><span class="step-title"></span>
    Now start the server again. For this guide I used the local network IP to login to the Project Zomboid server.
    In order for other people to connect over the internet to your server, you may need to redirect ports
    on your router. More information on that can be found in
    <a href="#additionalInformation" use:scrollto={'#additionalInformation'}>additional information</a>.
  </p>
  <p>
    After logging in I am greeted with the new Welcome Message I configured earlier. Also, if you have a
    Log Channel ID set in the discord bot configuration, you should see a login event message in that channel.
  </p>
  <pre class="pre is-thinner">!server start</pre>
  <figure><img src="/assets/setup/48_login_server_details.png" alt="Login Server Details" loading="lazy" /></figure>
  <figure><img src="/assets/setup/48_login_welcome_message.png" alt="Login Welcome Message" loading="lazy" /></figure>
  <figure><img src="/assets/setup/48_login_event.png" alt="Login Event" loading="lazy" /></figure>
</div>

<div class="content">
  <p><span class="step-title"></span>
    Try some server console commands now. Two examples shown below.
    You can broadcast a message to all players on the server.
    Items can also be spawned in a players inventory.
    See the help command for the full list of server console commands.
  </p>
  <pre class="pre is-thinner">!world broadcast Hello Everyone</pre>
  <pre class="pre is-thinner">!player Demo give-item Base Axe 2</pre>
  <figure><img src="/assets/setup/49_console_commands.png" alt="Console Commands" loading="lazy" /></figure>
  <figure><img src="/assets/setup/49_world_broadcast.png" alt="World Broadcast" loading="lazy" /></figure>
  <figure><img src="/assets/setup/49_give_item.png" alt="Give Item" loading="lazy" /></figure>
</div>


<div class="content" id="additionalInformation">
  <hr />
  <h3 class="title is-4">Additional Information</h3>
</div>

<div class="content" id="configurationFiles">
  <h4 class="title is-5">Configuration Files</h4>
  <p>
    For help understanding Project Zomboid server configuration files. Please see the
    <a href="https://steamcommunity.com/sharedfiles/filedetails/?id=2682570605" target="_blank">
    excellent guide on Steam <i class="fa fa-up-right-from-square"></i></a> by Aiteron.
    All of the configuration files can be downloaded using Discord using the commands shown below.
    Use the corresponding <span class="is-family-monospace">!setconfig</span> command to upload files.
  </p>
  <table class="table is-thinner">
    <thead>
      <tr><th>Download Command</th><th>Config File</th></tr>
    </thead>
    <tbody class="is-family-monospace">
      <tr><td>!getconfig ini</td><td>settings.ini</td></tr>
      <tr><td>!getconfig sandbox</td><td>settings_SandboxVars.lua</td></tr>
      <tr><td>!getconfig spawnregions</td><td>settings_spawnregions.lua</td></tr>
      <tr><td>!getconfig spawnpoints</td><td>settings_spawnpoints.lua</td></tr>
      <tr><td>!getconfig jvm</td><td>ProjectZomboid64.json</td></tr>
    </tbody>
  </table>
</div>

<div class="content" id="portForwarding">
  <h4 class="title is-5">Port Forwarding</h4>
  <p>
    In order for people to connect to your Project Zomboid server over the internet, your home
    router (internet gateway / &quot;modem&quot;) needs to be configured to forward ports to the server.
    <span class="is-italic">By default the server will automatically forward ports using UPnP.</span>
    However, if this is not working on your LAN, you can manually add the port forwarding.
  </p>
  <p>
    To do this, login to your router then forward ports as shown below. Use of the public IP address as shown
    on the ServerJockey console. More detailed instructions cannot be provided because each router will have
    a different webapp interface depending on the brand and model.
  </p>
  <table class="table is-thinner">
    <thead>
      <tr><th>Purpose</th><th>Port</th><th>Protocal</th></tr>
    </thead>
    <tbody class="is-family-monospace">
      <tr><td>Steam</td><td>16261</td><td>UDP</td></tr>
      <tr><td>Direct</td><td>16262</td><td>UDP</td></tr>
    </tbody>
  </table>
  <p>
    If using manual port forwarding you should also disable UPnP in the
    <span class="is-family-monospace">settings.ini</span> configuration file.
  </p>
  <pre class="pre is-thinner"
># Attempt to configure a UPnP-enabled internet gateway to automatically setup port forwarding rules.
# The server will fall back to default ports if this fails.
UPnP=false</pre>
</div>

<div class="content" id="memoryAllocation">
  <h4 class="title is-5">Memory Allocation</h4>
  <p>
    The Project Zomboid server has a memory allocation. This is defined in
    the <span class="is-family-monospace">ProjectZomboid64.json</span> file.
    Find the <span class="has-text-weight-bold">-Xmx</span> argument under
    <span class="has-text-weight-bold">vmArgs</span>. By default 8Gb is allocated. You can adjust as needed.
    As a general rule, the memory required is 2Gb + 500Mb per player. Whatever value is set,
    the machine that the server is running on should have 2Gb more of free memory.
  </p>
  <pre class="pre is-thinner">"vmArgs": [
    "-Djava.awt.headless=true",
    "-Xmx8g",
    "-Dzomboid.steam=1",
    "-Dzomboid.znetlog=1",
    "-Djava.library.path=linux64/:natives/",
    "-Djava.security.egd=file:/dev/urandom",
    "-XX:+UseZGC",
    "-XX:-OmitStackTraceInFastThrow"
]</pre>
</div>

<BackToTop />
