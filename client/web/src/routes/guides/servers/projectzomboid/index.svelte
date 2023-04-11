<script>
  import { scrollto } from 'svelte-scrollto-element';
</script>


<div class="content">
  <h2 class="title is-3 mt-2">Project Zomboid</h2>
  <p>
    This guide has 2 sections<br />
    <a href="#setup-with-bot" use:scrollto={'#setup-with-bot'}>Setup with Bot</a><br />
    <a href="#additional-information" use:scrollto={'#additional-information'}>Additional Information</a>
  </p>
</div>


<div class="content" id="setup-with-bot">
  <hr />
  <h3 class="title is-4">Setup Guide using the Discord bot</h3>
</div>

<div class="content">
  <p><span class="step-title">01.</span>
    Now try creating an instance again. For this guide I called the instance
    <span class="has-text-weight-bold">myserver</span>. You can give your instance a different name,
    but it must be lower case characters and numbers only, no spaces or special characters.
    The second command value is <span class="has-text-weight-bold">projectzomboid</span>.
    This is the type of instance.
  </p>
  <pre class="pre">!create myserver projectzomboid</pre>
  <figure><img src="/assets/setup/38_create_instance_success.png" alt="Create Instances Success" /></figure>
</div>

<div class="content">
  <p><span class="step-title">02.</span>
    Now enter the help command again. Now that there is an instance,
    you will see all the commands for that type of server.
  </p>
  <pre class="pre">!help</pre>
  <figure><img src="/assets/setup/39_help_pz.png" alt="Help PZ" /></figure>
</div>

<div class="content">
  <p><span class="step-title">03.</span>
    Although the instance has been created, the Project Zomboid server itself is not installed yet.
    The stable version can now be downloaded and installed with the command shown below.
    The bot reacts with an hourglass emoji initially as the process happens.
    Once complete, the hourglass will be replaced with a green tick.
    Also the log output from SteamCMD will be attached. You can check this to ensure the
    server was installed without issue.
  </p>
  <pre class="pre">!deployment install-runtime</pre>
  <figure><img src="/assets/setup/40_deploy_runtime_hourglass.png" alt="Deploy Runtime Hourglass" /></figure>
  <figure><img src="/assets/setup/40_deploy_runtime_success.png" alt="Deploy Runtime Success" /></figure>
</div>

<div class="content">
  <p><span class="step-title">04.</span>
    With the server installed, it can now be started with the following command. Same as the server install,
    an hourglass emoji is shown then replaced with a green tick when the server has fully started.
  </p>
  <pre class="pre">!server start</pre>
  <figure><img src="/assets/setup/41_server_start_hourglass.png" alt="Start Server Hourglass" /></figure>
  <figure><img src="/assets/setup/41_server_start_success.png" alt="Start Server Success" /></figure>
</div>

<div class="content">
  <p><span class="step-title">05.</span>
    You can check the status of the server at any time with the following command.
    Now that the server is up, the server version and connection details are shown.
  </p>
  <pre class="pre">!server</pre>
  <figure><img src="/assets/setup/42_server_status_up.png" alt="Server Status Up" /></figure>
</div>

<div class="content">
  <p><span class="step-title">06.</span>
    Before we continue to login and play, the server configuration needs attention. After starting the
    Project Zomboid server for the first time, the configuration files are created with default values.
    So stop the server with the following command.
  </p>
  <pre class="pre">!server stop</pre>
  <figure><img src="/assets/setup/43_server_stop.png" alt="Server Stop" /></figure>
</div>

<div class="content">
  <p><span class="step-title">07.</span>
    The server INI file can be downloaded as an attachment with the following command.
    See the server command list for other configuration files that can be downloaded.
  </p>
  <pre class="pre">!getconfig ini</pre>
  <figure><img src="/assets/setup/44_getconfig_ini.png" alt="Get Config INI" /></figure>
</div>

<div class="content">
  <p><span class="step-title">08.</span>
    For the purpose of this guide. I have only updated a the public server name and welcome message
    in the downloaded INI file. Typically you will make more changes. You can look at the
    <a href="#additional-information" use:scrollto={'#additional-information'}>additional information</a>
    at the end of this guide for more help on Project Zomboid server configuration.
  </p>
  <pre class="pre">PublicName=ZomBox demo server
ServerWelcomeMessage=Welcome to the ZomBox demo server.</pre>
</div>

<div class="content">
  <p><span class="step-title">09.</span>
    After making changes to the downloaded INI file. You can now upload it back to the server.
    Attach the INI file in Discord to upload it with the following command.
    Once again, the bot will react with a green tick emoji to show that the command was successful.
  </p>
  <pre class="pre">!setconfig ini</pre>
  <figure><img src="/assets/setup/46_setconfig_ini.png" alt="Set Config INI" /></figure>
</div>

<div class="content">
  <p><span class="step-title">10.</span>
    The server configuration has now been updated. However the server created a game world save (map)
    using the default configuration. You can delete the world with the following command.
  </p>
  <pre class="pre">!deployment wipe-world-save</pre>
  <figure><img src="/assets/setup/47_wipe_map.png" alt="Wipe Map" /></figure>
</div>

<div class="content">
  <p><span class="step-title">11.</span>
    Now start the server again. For this guide I used the local network IP to login to the Project Zomboid server.
    In order for other people to connect over the internet to your server, you need to redirect ports on your router.
    More information on that can be found in
    <a href="#additional-information" use:scrollto={'#additional-information'}>additional information</a>.
  </p>
  <p>
    After logging in I am greeted with the new Welcome Message I configured earlier.
    Also, if you set a Log Channel ID in the bot setup you should see a login event in that channel.
  </p>
  <pre class="pre">!server start</pre>
  <figure><img src="/assets/setup/48_login_server_details.png" alt="Login Server Details" /></figure>
  <figure><img src="/assets/setup/48_login_welcome_message.png" alt="Login Welcome Message" /></figure>
  <figure><img src="/assets/setup/48_login_event.png" alt="Login Event" /></figure>
</div>

<div class="content">
  <p><span class="step-title">12.</span>
    Try some server console commands now. Two examples shown below.
    You can broadcast a message to all players on the server.
    Items can also be spawned in a players inventory.
    See the help command for the full list of server console commands.
  </p>
  <pre class="pre">!world broadcast Hello Everyone</pre>
  <pre class="pre">!player Demo give-item Base Axe 2</pre>
  <figure><img src="/assets/setup/49_console_commands.png" alt="Console Commands" /></figure>
  <figure><img src="/assets/setup/49_world_broadcast.png" alt="World Broadcast" /></figure>
  <figure><img src="/assets/setup/49_give_item.png" alt="Give Item" /></figure>
</div>


<div class="content" id="additional-information">
  <hr />
  <h3 class="title is-4">Additional Information</h3>
</div>

<div class="content">
  <h4 class="title is-5">Configuration Files</h4>
  <p>
    For help understanding Project Zomboid server configuration files. Please see the
    <a href="https://steamcommunity.com/sharedfiles/filedetails/?id=2682570605" target="_blank">
    excellent guide on Steam</a> by Aiteron.
    All of the configuration files can be downloaded using Discord using the commands shown below.
    Use the corresponding <span class="is-family-monospace">!setconfig</span> command to upload files.
  </p>
  <table class="table">
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

<div class="content">
  <h4 class="title is-5">Port Forwarding</h4>
  <p>
    In order for people to connect to your Project Zomboid server over the internet, your home
    router (internet gateway / &quot;modem&quot;) needs to be configured to forward ports to the server.
    By default the server will automatically forward ports using UPnP. However, if this is not
    working on your LAN, you can manually add the port forwarding.
  </p>
  <p>
    To do this, login to your router then forward ports as shown below. Use of the IP address as shown
    on the ServerJockey console. More detailed instructions cannot be provided because each router will have
    a different webapp interface depending on the brand and model.
  </p>
  <table class="table">
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
  <pre class="pre"># Attempt to configure a UPnP-enabled internet gateway to automatically setup port forwarding rules.
# The server will fall back to default ports if this fails.
UPnP=false</pre>
</div>

<div class="content">
  <h4 class="title is-5">Memory Allocation</h4>
  <p>
    The Project Zomboid server that runs inside ServerJockey also has a memory allocation.
    This is defined in the <span class="is-family-monospace">ProjectZomboid64.json</span> file.
    Find the <span class="has-text-weight-bold">-Xmx</span>
    argument under <span class="has-text-weight-bold">vmArgs</span>.
    By default 8Gb is allocated. You can adjust as needed.
    As a general rule, the memory required is 2Gb + 500Mb per player.
    Whatever value is set, the ZomBox memory allocation should be 1Gb more.
  </p>
  <pre class="pre">"vmArgs": [
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
