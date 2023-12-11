<script>
  import { scrollto } from 'svelte-scrollto-next';
  import BackToTop from '$lib/BackToTop.svelte';
  import Clyde from '$lib/Clyde.svelte';
  import CodeBlock from '$lib/CodeBlock.svelte';
</script>


<div class="columns">
  <div class="column is-one-quarter content mb-0">
    <figure class="image ml-5 mr-5 mt-3 max-300"><Clyde /></figure>
  </div>
  <div class="column is-three-quarters content">
    <h2 class="title is-3 mt-2">Discord Bot Usage</h2>
    <p>
      This guide covers installing, configuring and starting a Project Zomboid server using Discord.
      You will need to <a href="/guides/discord/setup">setup the discord bot</a> first if you have not already.
    </p>
    <p>
      If you are following this guide after the discord bot setup guide, then an instance already exists, so you can
      <a href="#setupWithBotTwo" use:scrollto={'#setupWithBotTwo'}>jump to the second step</a>.
      Otherwise start at the <a href="#setupWithBotOne" use:scrollto={'#setupWithBotOne'}>first step</a> to begin.
    </p>
  </div>
</div>

<div class="content" id="setupWithBotOne">
  <hr />
  <h3 class="title is-4">Server setup using the Discord bot</h3>
</div>

<div class="content">
  <p><span class="step-title"></span>
    First step is to create an instance for the server.
    For this guide the instance is called <span class="has-text-weight-bold">myserver</span>.
    The name must be lower case letters and numbers, no spaces or special characters except dashes and underscores.
    The second value is <span class="has-text-weight-bold">projectzomboid</span>.
    This is the module, which is a supported game server. In this case, Project Zomboid.
    So this instance will be for a Project Zomboid server.
  </p>
  <CodeBlock>!create myserver projectzomboid</CodeBlock>
  <figure class="image max-800">
    <img src="/assets/setup/38_create_instance_success.png" alt="Create Instances Success" />
  </figure>
</div>

<div class="content" id="setupWithBotTwo">
  <p><span class="step-title"></span>
    With an instance created, you can now view all of the commands
    for that type (module) of instance using the help command.
  </p>
  <CodeBlock>!help</CodeBlock>
  <figure class="image max-800">
    <img src="/assets/setup/39_help_pz.png" alt="Help PZ" loading="lazy" />
  </figure>
</div>

<div class="content">
  <p><span class="step-title"></span>
    Although the instance has been created, the Project Zomboid server itself is not installed yet.
    The stable version can now be downloaded and installed with the command shown below. The bot reacts
    with an hourglass emoji initially as the process happens. Once complete, the hourglass will be replaced
    with a green tick. Also the log output from SteamCMD will be attached. You can check this to ensure
    the server was installed without issue.
  </p>
  <CodeBlock>!deployment install-runtime</CodeBlock>
  <figure class="image max-800">
    <img src="/assets/setup/40_deploy_runtime_hourglass.png" alt="Deploy Runtime Hourglass" loading="lazy" />
  </figure>
  <figure class="image max-800">
    <img src="/assets/setup/40_deploy_runtime_success.png" alt="Deploy Runtime Success" loading="lazy" />
  </figure>
</div>

<div class="content">
  <p><span class="step-title"></span>
    With the server installed, it can now be started with the following command. Same as the server install,
    an hourglass emoji is shown then replaced with a green tick when the server has fully started.
  </p>
  <CodeBlock>!server start</CodeBlock>
  <figure class="image max-800">
    <img src="/assets/setup/41_server_start_hourglass.png" alt="Start Server Hourglass" loading="lazy" />
  </figure>
  <figure class="image max-800">
    <img src="/assets/setup/41_server_start_success.png" alt="Start Server Success" loading="lazy" />
  </figure>
</div>

<div class="content">
  <p><span class="step-title"></span>
    You can check the status of the server at any time with the following command.
    Now that the server is up, the server version and connection details are shown.
  </p>
  <CodeBlock>!server</CodeBlock>
  <figure class="image max-800">
    <img src="/assets/setup/42_server_status_up.png" alt="Server Status Up" loading="lazy" />
  </figure>
</div>

<div class="content">
  <p><span class="step-title"></span>
    Before we continue to login and play, the server configuration needs attention. After starting the
    Project Zomboid server for the first time, the configuration files are created with default values.
    So stop the server with the following command.
  </p>
  <CodeBlock>!server stop</CodeBlock>
  <figure class="image max-800">
    <img src="/assets/setup/43_server_stop.png" alt="Server Stop" loading="lazy" />
  </figure>
</div>

<div class="content">
  <p><span class="step-title"></span>
    The server INI file can be downloaded as an attachment with the following command.
    See the server command list for other configuration files that can be downloaded.
    Save this file to disk somewhere to edit it.
  </p>
  <CodeBlock>!getconfig ini</CodeBlock>
  <figure class="image max-800">
    <img src="/assets/setup/44_getconfig_ini.png" alt="Get Config INI" loading="lazy" />
  </figure>
</div>

<div class="content">
  <p><span class="step-title"></span>
    For the purpose of this guide. I only updated a the public server name
    and welcome message in the downloaded INI file.
  </p>
  <CodeBlock>PublicName=ZomBox demo server
ServerWelcomeMessage=Welcome to the ZomBox demo server.</CodeBlock>
</div>

<div class="content">
  <p><span class="step-title"></span>
    After making changes to the downloaded INI file. You can now upload it back to the server.
    Attach the INI file in Discord to upload it with the following command.
    Once again, the bot will react with a green tick emoji to show that the command was successful.
  </p>
  <CodeBlock>!setconfig ini</CodeBlock>
  <figure class="image max-800">
    <img src="/assets/setup/46_setconfig_ini.png" alt="Set Config INI" loading="lazy" />
  </figure>
</div>

<div class="content">
  <p><span class="step-title"></span>
    The server configuration has now been updated. However the server created a game world (map files)
    using the default configuration. You can delete the world with the following command.
  </p>
  <CodeBlock>!deployment wipe-world-save</CodeBlock>
  <figure class="image max-800">
    <img src="/assets/setup/47_wipe_map.png" alt="Wipe Map" loading="lazy" />
  </figure>
</div>

<div class="content">
  <p><span class="step-title"></span>
    Now start the server again. For this guide I used the local network IP to login to the Project Zomboid server.
    After logging in I am greeted with the new Welcome Message I configured earlier. Also, if you have the
    Player Event Channel ID set in the discord bot configuration, you should see a login event message in that channel.
  </p>
  <CodeBlock>!server start</CodeBlock>
  <figure class="image max-800">
    <img src="/assets/setup/48_login_server_details.png" alt="Login Server Details" loading="lazy" />
  </figure>
  <figure class="image max-800">
    <img src="/assets/setup/48_login_welcome_message.png" alt="Login Welcome Message" loading="lazy" />
  </figure>
  <figure class="image max-800">
    <img src="/assets/setup/48_login_event.png" alt="Login Event" loading="lazy" />
  </figure>
</div>

<div class="content">
  <p><span class="step-title"></span>
    Now try some server console commands. Two examples are shown below.
    You can broadcast a message to all players on the server.
    Items can also be spawned in a players inventory.
    Use the help command for the full list of server console commands.
  </p>
  <CodeBlock>!world broadcast Hello Everyone</CodeBlock>
  <CodeBlock>!player Demo give-item Base Axe 2</CodeBlock>
  <figure class="image max-800">
    <img src="/assets/setup/49_console_commands.png" alt="Console Commands" loading="lazy" />
  </figure>
  <figure class="image max-800">
    <img src="/assets/setup/49_world_broadcast.jpg" alt="World Broadcast" loading="lazy" />
  </figure>
  <figure class="image max-800">
    <img src="/assets/setup/49_give_item.png" alt="Give Item" loading="lazy" />
  </figure>
</div>

<BackToTop />
