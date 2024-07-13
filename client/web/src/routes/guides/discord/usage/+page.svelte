<script>
  import { scrollto } from 'svelte-scrollto-next';
  import { surl } from '$lib/util/sjgmsapi';
  import Clyde from '$lib/svg/Clyde.svelte';
  import BackToTop from '$lib/widget/BackToTop.svelte';
  import CodeBlock from '$lib/widget/CodeBlock.svelte';
</script>


<div class="columns">
  <div class="column is-one-quarter content mb-0">
    <figure class="image ml-5 mr-5 mt-3 max-300"><Clyde /></figure>
  </div>
  <div class="column is-three-quarters content">
    <h2 class="title is-3 mt-2">Discord Bot Usage</h2>
    <p>
      This guide covers installing, configuring and starting a Project Zomboid server using Discord. You will need to
      <a href={surl('/guides/discord/setup')}>setup the discord bot</a>
      first if you have not already.
    </p>
    <p>
      If you are following this guide after the discord bot setup guide, then an instance already exists, so you can
      <a href="#setupWithBotTwo" use:scrollto={'#setupWithBotTwo'}>jump to the second step</a>.
      Otherwise start at the
      <a href="#setupWithBotOne" use:scrollto={'#setupWithBotOne'}>first step</a>
      to begin.
    </p>
  </div>
</div>

<div class="content" id="setupWithBotOne">
  <hr />
  <p><span class="step-title"></span>
    First step is to create an instance for the server. For the guide the instance is called
    <span class="has-text-weight-bold notranslate">myserver</span>.
    The name must be lower case letters and numbers, no spaces or special characters except dashes and underscores.
    The second value is
    <span class="has-text-weight-bold notranslate">projectzomboid</span>.
    This is the module, which is a supported game server. So this instance will be for a Project Zomboid server.
  </p>
  <CodeBlock>!create myserver projectzomboid</CodeBlock>
  <figure class="image max-800">
    <img src={surl('/assets/guides/discord/setup/create_instance_success.png')}
         alt="Create Instances Success" />
  </figure>
</div>

<div class="content" id="setupWithBotTwo">
  <p><span class="step-title"></span>
    With an instance created, you can now view all of the commands available for the instance using the help command.
  </p>
  <CodeBlock>!help</CodeBlock>
  <figure class="image max-800">
    <img src={surl('/assets/guides/discord/usage/help_pz.png')}
         alt="Help PZ" loading="lazy" />
  </figure>
</div>

<div class="content">
  <p><span class="step-title"></span>
    Although the instance has been created, the Project Zomboid server itself is not installed yet.
    The stable version can now be downloaded and installed with the command shown below. The bot initally reacts
    with an hourglass emoji for the process, then replaces it with a green tick when complete. Also the log output
    from SteamCMD will be attached. Check the log to ensure the server was installed without issue.
  </p>
  <CodeBlock>!deployment install-runtime</CodeBlock>
  <figure class="image max-800">
    <img src={surl('/assets/guides/discord/usage/deploy_runtime_hourglass.png')}
         alt="Deploy Runtime Hourglass" loading="lazy" />
  </figure>
  <figure class="image max-800">
    <img src={surl('/assets/guides/discord/usage/deploy_runtime_success.png')}
         alt="Deploy Runtime Success" loading="lazy" />
  </figure>
</div>

<div class="content">
  <p><span class="step-title"></span>
    With the server installed, it can now be started with the following command.
  </p>
  <CodeBlock>!server start</CodeBlock>
  <figure class="image max-800">
    <img src={surl('/assets/guides/discord/usage/server_start_success.png')}
         alt="Start Server Success" loading="lazy" />
  </figure>
</div>

<div class="content">
  <p><span class="step-title"></span>
    You can check the status of the server at any time with the following command.
    Now that the server is up, the server version and connection details are shown.
  </p>
  <CodeBlock>!server</CodeBlock>
  <figure class="image max-800">
    <img src={surl('/assets/guides/discord/usage/server_status_up.png')}
         alt="Server Status Up" loading="lazy" />
  </figure>
</div>

<div class="content">
  <p><span class="step-title"></span>
    Before you login and play, the server configuration needs attention.
    After starting the Project Zomboid server for the first time, the configuration files
    are created with default values. Stop the server with the following command.
  </p>
  <CodeBlock>!server stop</CodeBlock>
  <figure class="image max-800">
    <img src={surl('/assets/guides/discord/usage/server_stop.png')}
         alt="Server Stop" loading="lazy" />
  </figure>
</div>

<div class="content">
  <p><span class="step-title"></span>
    The server INI file can be downloaded as an attachment with the following command.
    Save this file to disk somewhere to edit it.
  </p>
  <CodeBlock>!getconfig ini</CodeBlock>
  <figure class="image max-800">
    <img src={surl('/assets/guides/discord/usage/getconfig_ini.png')}
         alt="Get Config INI" loading="lazy" />
  </figure>
</div>

<div class="content">
  <p><span class="step-title"></span>
    For the purpose of the guide, I only updated the public server name and welcome message in the downloaded INI file.
  </p>
  <CodeBlock nocopy>
PublicName=ServerJockey guide server
ServerWelcomeMessage=Welcome to the ServerJockey guide server.</CodeBlock>
</div>

<div class="content">
  <p><span class="step-title"></span>
    After making changes to the downloaded INI file, you can now upload it back to the server.
    Attach the INI file in Discord to upload it with the following command.
  </p>
  <CodeBlock>!setconfig ini</CodeBlock>
  <figure class="image max-800">
    <img src={surl('/assets/guides/discord/usage/setconfig_ini.png')}
         alt="Set Config INI" loading="lazy" />
  </figure>
</div>

<div class="content">
  <p><span class="step-title"></span>
    The server configuration has now been updated. However the server created a game world save (map files)
    using the default configuration. You can delete the world with the following command.
  </p>
  <CodeBlock>!deployment wipe-world-save</CodeBlock>
  <figure class="image max-800">
    <img src={surl('/assets/guides/discord/usage/wipe_map.png')}
         alt="Wipe Map" loading="lazy" />
  </figure>
</div>

<div class="content">
  <p><span class="step-title"></span>
    Now start the server again. For the guide I used the local network IP to connect. After login I am greeted
    with the new welcome message I configured earlier. Also, if you have the Player Event Channel ID set in the
    discord bot configuration, you should see a login event message in that channel.
  </p>
  <CodeBlock>!server start</CodeBlock>
  <figure class="image max-800">
    <img src={surl('/assets/guides/discord/usage/login_server_details.png')}
         alt="Login Server Details" loading="lazy" />
  </figure>
  <figure class="image max-600">
    <img src={surl('/assets/guides/discord/usage/login_welcome_message.png')}
         alt="Login Welcome Message" loading="lazy" />
  </figure>
  <figure class="image max-800">
    <img src={surl('/assets/guides/discord/usage/login_event.png')}
         alt="Login Event" loading="lazy" />
  </figure>
</div>

<div class="content">
  <p><span class="step-title"></span>
    Now try some server console commands. Two examples are shown below.
    You can broadcast a message to all players on the server. Items can also be spawned in a players inventory.
    Use the help command for the full list of server console commands.
  </p>
  <CodeBlock>!world broadcast Hello everyone</CodeBlock>
  <CodeBlock>!player GuidePlayer give-item Base Axe 2</CodeBlock>
  <figure class="image max-800">
    <img src={surl('/assets/guides/discord/usage/console_commands.png')}
         alt="Console Commands" loading="lazy" />
  </figure>
  <figure class="image max-800">
    <img src={surl('/assets/guides/discord/usage/world_broadcast.jpg')}
         alt="World Broadcast" loading="lazy" />
  </figure>
  <figure class="image max-600">
    <img src={surl('/assets/guides/discord/usage/give_item.png')}
         alt="Give Item" loading="lazy" />
  </figure>
</div>

<BackToTop />
