<script>
  import { scrollto } from 'svelte-scrollto-element';
  import { onMount, onDestroy } from 'svelte';
  import { baseurl, instance, serverStatus, SubscriptionHelper, newGetRequest } from '$lib/serverjockeyapi';
  import ServerStatus from '$lib/ServerStatus.svelte';
  import ServerControls from '$lib/ServerControls.svelte';
  import ServerLinkConfig from '$lib/ServerLinkConfig.svelte';

  instance.set({ url: baseurl + '/instances/serverlink' }); // used by ServerControls
  serverStatus.set({}); // used by ServerControls
  let subs = new SubscriptionHelper();

	onMount(async function() {
    const result = await fetch(baseurl + '/instances/serverlink/server', newGetRequest())
      .then(function(response) {
         if (!response.ok) throw new Error('Status: ' + response.status);
        return response.json();
      })
      .catch(function(error) { alert('Error: ' + error); });
    serverStatus.set(result);
    await subs.start(baseurl + '/instances/serverlink/server/subscribe', function(data) {
      serverStatus.set(data);
	    return true;
	  });
	});

	onDestroy(function() {
		subs.stop();
	});
</script>


<div class="columns">
  <div class="column is-one-third">
    <figure><img src="/assets/box.svg" alt="Welcome Box" /></figure>
  </div>
  <div class="column content">
    <h2 class="title is-3 mt-2">Welcome</h2>
    <p>
      If you are reading this, you have already successfully installed and started ZomBox on VirtualBox. Congratulations!
      This page will guide you through the rest of the setup process and how to create, configure and start a server.
    </p>
    <p>
      Although this guide will walk you through process carefully, some prerequisite game server knowledge is
      still required. You will need to be familiar with editing Project Zomboid server configuration files.
      Also you may have to know how to forward ports on your router.
      However <a href="#additionalinformation" use:scrollto={'#additionalinformation'}>additional information</a>
      is included at the end of the guide to help with these.
    </p>
  </div>
</div>


<div class="content">
  <hr />
  <p><span class="step-title">01.</span>
    First step is to <a href="https://discord.com/login" target="_blank">login to Discord</a> in your browser.
    If you don't have an account then <a href="https://discord.com/register" target="_blank">register</a> a new one.
    Below is screenshot of a fresh account for the guide. You now need your own Discord server.
    If you already have one, <a href="#createbot" use:scrollto={'#createbot'}>skip to the bot step</a>.
    If not, create a new Discord server in the
    <a href="#newdiscordserver" use:scrollto={'#newdiscordserver'}>next step</a>.
  </p>
  <figure><img src="/instructions/01_new_account.png" alt="New Discord Account" /></figure>
</div>

<div class="content" id="newdiscordserver">
  <p><span class="step-title">02.</span>
    Add a new Discord server by clicking the <span class="is-family-monospace is-size-5">+</span> button
    on the left panel.
  </p>
  <figure><img src="/instructions/02_add_server_button.png" alt="Add a Server" /></figure>
</div>

<div class="content">
  <p><span class="step-title">03.</span>
    Select the <span class="has-text-weight-bold">Create My Own</span> option.
  </p>
  <figure><img src="/instructions/03_create_server_options.png" alt="Create Server Options" /></figure>
</div>

<div class="content">
  <p><span class="step-title">04.</span>
    Choose the kind of Discord server you want, or skip to choose later.
  </p>
  <figure><img src="/instructions/04_choose_server_type.png" alt="Choose Server Type" /></figure>
</div>

<div class="content">
  <p><span class="step-title">05.</span>
    Give your new Discord server a name. Can be anything that Discord allows.
  </p>
  <figure><img src="/instructions/05_name_server.png" alt="Name the Server" /></figure>
</div>

<div class="content">
  <p><span class="step-title">06.</span>
    You should now have a new Discord server. It should look like the screenshot below.
    For the guide, I called the server ZomBoxGuide. Not very original, I know.
  </p>
  <figure><img src="/instructions/06_fresh_server.png" alt="Fresh Discord Server" /></figure>
</div>

<div class="content" id="createbot">
  <p><span class="step-title">07.</span>
    Now that a new or existing Discord server is ready. It is time to create a Discord bot.
    Don't worry! No coding is required, that is all in the ZomBox. This is the bot setup on Discord.
    Similar to how users register an account to login, bots also need to be registered to login.
  </p>
  <p>
    To start the setup process.
    Open the <a href="https://discord.com/developers" target="_blank">Discord Developer Portal</a>.
    Then click the <span class="has-text-weight-bold">New Application</span> button.
  </p>
  <figure><img src="/instructions/07_developers_home.png" alt="Discord Developer Portal" /></figure>
</div>

<div class="content">
  <p><span class="step-title">08.</span>
    Give your application a name. It can be anything that Discord allows.
    For the guide, I called it zombox-demo.
  </p>
  <figure><img src="/instructions/08_name_application.png" alt="Name New App" /></figure>
</div>

<div class="content">
  <p><span class="step-title">09.</span>
    You should now have a new Discord application. It should look like the screenshot below.
  </p>
  <figure><img src="/instructions/09_fresh_application.png" alt="Fresh App" /></figure>
</div>

<div class="content">
  <p><span class="step-title">10.</span>
    In the <span class="has-text-weight-bold">SETTINGS</span> on the left panel,
    select the <span class="has-text-weight-bold">Bot</span> section.
    Then click the <span class="has-text-weight-bold">Add Bot</span> button.
  </p>
  <figure><img src="/instructions/10_add_bot.png" alt="Add a Bot" /></figure>
</div>

<div class="content">
  <p><span class="step-title">11.</span>
    Click the <span class="has-text-weight-bold">Yes, do it!</span> button to confirm adding the bot to the application.
  </p>
  <figure><img src="/instructions/11_accept_new_bot.png" alt="Accept New Bot" /></figure>
</div>

<div class="content">
  <p><span class="step-title">12.</span>
     You should now have a new Discord bot. It should look like the screenshot below.
  </p>
  <figure><img src="/instructions/12_fresh_bot.png" alt="Fresh Bot" /></figure>
</div>

<div class="content">
  <p><span class="step-title">13.</span>
    Scroll down the bot settings to find the <span class="has-text-weight-bold">PUBLIC BOT</span> switch.
    Turn it off, then click <span class="has-text-weight-bold">Save Changes</span> button.
  </p>
  <figure><img src="/instructions/13_make_bot_private.png" alt="Make Bot Private" /></figure>
</div>

<div class="content">
  <p><span class="step-title">14.</span>
    With the new bot created, it's time to invite the bot to your Discord server.
    In the <span class="has-text-weight-bold">SETTINGS</span> on the left panel,
    select the <span class="has-text-weight-bold">OAuth2</span> section.
    Then select the <span class="has-text-weight-bold">URL Generator</span> under that.
    Now on the right panel, in <span class="has-text-weight-bold">SCOPES</span>,
    check the <span class="has-text-weight-bold">bot</span> checkbox.
  </p>
  <figure><img src="/instructions/14_bot_invite_scope.png" alt="Set Bot Scope" /></figure>
</div>

<div class="content">
  <p><span class="step-title">15.</span>
    Scroll down to <span class="has-text-weight-bold">BOT PERMISSIONS</span>.
    Then check all the checkboxes as shown in the screenshot below.
    Now click the <span class="has-text-weight-bold">Copy</span> button
    to copy the generated invite URL.
  </p>
  <figure><img src="/instructions/15_bot_invite_perms.png" alt="Set Bot Perms" /></figure>
</div>

<div class="content">
  <p><span class="step-title">16.</span>
    Open a new tab in your browser. Paste the URL into the address bar and hit enter.
  </p>
  <figure><img src="/instructions/16_bot_invite_url.png" alt="Invite Bot" /></figure>
</div>

<div class="content">
  <p><span class="step-title">17.</span>
    Choose your Discord server from the dropdown list.
    Then click the <span class="has-text-weight-bold">Continue</span> button.
  </p>
  <figure><img src="/instructions/17_bot_invite_choose_server.png" alt="Choose Server for Bot" /></figure>
</div>

<div class="content">
  <p><span class="step-title">18.</span>
    Click the <span class="has-text-weight-bold">Authorize</span> button to complete the bot invite.
  </p>
  <figure><img src="/instructions/18_bot_invite_authorize.png" alt="Authorise Bot" /></figure>
</div>

<div class="content">
  <p><span class="step-title">19.</span>
    Your new bot has now joined your Discord server!
  </p>
  <figure><img src="/instructions/19_bot_invite_authorized.png" alt="Bot Authorised" /></figure>
</div>

<div class="content">
  <p><span class="step-title">20.</span>
    Now go to the Discord server browser tab. You should now see the bot as a member on the right panel.
    It will be offline, that is expected.
  </p>
  <figure><img src="/instructions/20_bot_invite_fresh.png" alt="Bot Invited" /></figure>
</div>

<div class="content">
  <p><span class="step-title">21.</span>
    Before starting up the bot, it is recommended that you enable the developer features on Discord.
    This will allow you to see the channel IDs. If already enabled or you don't want to do this then
    skip to the <a href="#getbottoken" use:scrollto={'#getbottoken'}>get bot login token</a> step.
  </p>
  <p>
    To enable, open <span class="has-text-weight-bold">User Settings</span> with the cog button.
  </p>
  <figure><img src="/instructions/21_open_settings.png" alt="Open Discord Settings" /></figure>
</div>

<div class="content">
  <p><span class="step-title">22.</span>
    Select the <span class="has-text-weight-bold">Advanced</span> section in the left panel.
    Then switch on <span class="has-text-weight-bold">Developer Mode</span>.
    Now click the <span class="has-text-weight-bold">ESC</span> button at the top right to close Settings.
  </p>
  <figure><img src="/instructions/22_enable_developer_mode.png" alt="Enable Developer Mode" /></figure>
</div>

<div class="content">
  <p><span class="step-title">23.</span>
    With Developer Mode enabled. If you right-click on a Channel, there is now a menu option to Copy ID.
    This will be useful later on.
  </p>
  <figure><img src="/instructions/23_copy_channel_id.png" alt="Copy Channel ID" /></figure>
</div>

<div class="content" id="getbottoken">
  <p><span class="step-title">24.</span>
    Time to startup the bot. First a login token is needed. Go to the Developer Portal browser tab again.
    In the <span class="has-text-weight-bold">Bot</span> section click
    the <span class="has-text-weight-bold">Reset Token</span> button.
    This will reset and generate a new token.
  </p>
  <figure><img src="/instructions/24_reset_bot_token.png" alt="Reset Bot Token" /></figure>
</div>

<div class="content">
  <p><span class="step-title">25.</span>
    Click the <span class="has-text-weight-bold">Yes, do it!</span> button to confirm.
  </p>
  <figure><img src="/instructions/25_accept_reset_bot_token.png" alt="Accept Reset Bot Token" /></figure>
</div>

<div class="content">
  <p><span class="step-title">26.</span>
    Now click the <span class="has-text-weight-bold">Copy</span> button to copy the new token.
    Do not share this token with anyone.
  </p>
  <figure><img src="/instructions/26_copy_bot_token.png" alt="Copy Bot Token" /></figure>
</div>

<div class="content">
  <p><span class="step-title">27.</span>
    Paste the token into the <span class="has-text-weight-bold">Discord Bot Token</span> field in the form below.
    Optionally copy and paste a Channel ID into the <span class="has-text-weight-bold">Log Channel ID</span> field.
    Then click the <span class="has-text-weight-bold">Apply</span> button to save changes.
  </p>
</div>
<hr />
<div class="columns is-mobile is-centered">
  <div class="column is-11">
    <ServerLinkConfig />
  </div>
</div>
<hr />

<div class="content">
  <p><span class="step-title">28.</span>
    Finally time to start the bot. Don't worry if you first see an error below.
    The bot failed to login when you started ZomBox for the first time because no login token was set.
    It is now, so click the <span class="has-text-weight-bold">Start</span> button.
  </p>
</div>
<hr />
<div class="columns is-mobile is-centered">
  <div class="column is-11">
    <ServerStatus />
    <ServerControls />
  </div>
</div>
<hr />

<div class="content">
  <p><span class="step-title">29.</span>
    Go to the Discord server browser tab again. You should now see the bot online on the right panel.
    Congratulations making it this far!
  </p>
  <figure><img src="/instructions/29_bot_logged_in.png" alt="Bot Logged In" /></figure>
</div>

<div class="content">
  <p><span class="step-title">30.</span>
    Now it's time to try out the bot and learn how to create and manage a Project Zomboid server.
    The bot will work from any channel it has access to. First try the help command as shown below.
    The bot should reply with available commands.
  </p>
  <pre class="pre">!help</pre>
  <figure><img src="/instructions/30_help_system.png" alt="System Help" /></figure>
</div>

<div class="content">
  <p><span class="step-title">31.</span>
    Now try the instances command. An instance is a server container. This command will list them all.
    The response shows none are found because no instance has been created yet.
  </p>
  <pre class="pre">!instances</pre>
  <figure><img src="/instructions/31_instances_empty.png" alt="Instances Empty" /></figure>
</div>

<div class="content">
  <p><span class="step-title">32.</span>
    Try creating an instance now as shown below. The bot reacts with a lock emoji which means it didn't work!
    This is expected, you aren't authorised to create a server yet. Next steps will remedy this.
  </p>
  <pre class="pre">!create myserver projectzomboid</pre>
  <figure><img src="/instructions/32_create_instance_locked.png" alt="Create Instances Locked" /></figure>
</div>

<div class="content">
  <p><span class="step-title">33.</span>
    Right click on your Discord server in the left panel.
    Find <span class="has-text-weight-bold">Server Settings</span>
    then click on <span class="has-text-weight-bold">Roles</span>.
  </p>
  <figure><img src="/instructions/33_open_roles.png" alt="Open Roles" /></figure>
</div>

<div class="content">
  <p><span class="step-title">34.</span>
    Click the <span class="has-text-weight-bold">Create Role</span> button.
  </p>
  <figure><img src="/instructions/34_create_role_new.png" alt="Create New Role" /></figure>
</div>

<div class="content">
  <p><span class="step-title">35.</span>
    Enter a role name of <span class="is-family-monospace">pzadmin</span>. It must be named this.
    Now <span class="has-text-weight-bold">Save Changes</span>
    then select the <span class="has-text-weight-bold">Manage Members</span> tab.
  </p>
  <figure><img src="/instructions/35_create_pzadmin_role.png" alt="Create PZAdmin Role" /></figure>
</div>

<div class="content">
  <p><span class="step-title">36.</span>
    Click the <span class="has-text-weight-bold">Add Members</span> button.
  </p>
  <figure><img src="/instructions/36_add_member.png" alt="Add Members to Role" /></figure>
</div>

<div class="content">
  <p><span class="step-title">37.</span>
    Add yourself and any other members on your Discord server that you want access to manage
    your Project Zomboid server. Then click <span class="has-text-weight-bold">Add</span> button.
    Optionally you can select the <span class="has-text-weight-bold">Permissions</span> tab
    and make changes as you want. When done click the <span class="has-text-weight-bold">ESC</span>
    button at the top right to close Settings.
  </p>
  <figure><img src="/instructions/37_choose_member.png" alt="Choose Members for Role" /></figure>
</div>

<div class="content">
  <p><span class="step-title">38.</span>
    Now try creating an instance again. For this guide I called the instance
    <span class="has-text-weight-bold">myserver</span>. You can give your instance a different name,
    but it must be lower case characters and numbers only, no spaces or special characters.
    The second command value is <span class="has-text-weight-bold">projectzomboid</span>.
    This is the type of instance. Currently only Project Zomboid is supported so it must be this.
  </p>
  <p>
    Once created the bot will respond with the instances list.
    The arrow will mark the current selected instance.
  </p>
  <pre class="pre">!create myserver projectzomboid</pre>
  <figure><img src="/instructions/38_create_instance_success.png" alt="Create Instances Success" /></figure>
</div>

<div class="content">
  <p><span class="step-title">39.</span>
    Now enter the help command again. Now that there is an instance,
    you will see all the commands for that type of server.
  </p>
  <pre class="pre">!help</pre>
  <figure><img src="/instructions/39_help_pz.png" alt="Help PZ" /></figure>
</div>

<div class="content">
  <p><span class="step-title">40.</span>
    Although the instance has been created, the Project Zomboid server itself is not installed yet.
    The stable version can now be downloaded and installed with the command shown below.
    The bot reacts with an hourglass emoji initially as the process happens.
    Once complete, the hourglass will be replaced with a green tick.
    Also the log output from SteamCMD will be attached. You can check this to ensure the
    server was installed without issue.
  </p>
  <pre class="pre">!deployment install-runtime</pre>
  <figure><img src="/instructions/40_deploy_runtime_hourglass.png" alt="Deploy Runtime Hourglass" /></figure>
  <figure><img src="/instructions/40_deploy_runtime_success.png" alt="Deploy Runtime Success" /></figure>
</div>

<div class="content">
  <p><span class="step-title">41.</span>
    With the server installed, it can now be started with the following command. Same as the server install,
    an hourglass emoji is shown then replaced with a green tick when the server has fully started.
  </p>
  <pre class="pre">!server start</pre>
  <figure><img src="/instructions/41_server_start_hourglass.png" alt="Start Server Hourglass" /></figure>
  <figure><img src="/instructions/41_server_start_success.png" alt="Start Server Success" /></figure>
</div>

<div class="content">
  <p><span class="step-title">42.</span>
    You can check the status of the server at any time with the following command.
    Now that the server is up, the server version and connection details are shown.
  </p>
  <pre class="pre">!server</pre>
  <figure><img src="/instructions/42_server_status_up.png" alt="Server Status Up" /></figure>
</div>

<div class="content">
  <p><span class="step-title">43.</span>
    Before we continue to login and play, the server configuration needs attention. After starting the
    Project Zomboid server for the first time, the configuration files are created with default values.
    So stop the server with the following command.
  </p>
  <pre class="pre">!server stop</pre>
  <figure><img src="/instructions/43_server_stop.png" alt="Server Stop" /></figure>
</div>

<div class="content">
  <p><span class="step-title">44.</span>
    The server INI file can be downloaded as an attachment with the following command.
    See the server command list for other configuration files that can be downloaded.
  </p>
  <pre class="pre">!getconfig ini</pre>
  <figure><img src="/instructions/44_getconfig_ini.png" alt="Get Config INI" /></figure>
</div>

<div class="content">
  <p><span class="step-title">45.</span>
    For the purpose of this guide. I have only updated a the public server name and welcome message
    in the downloaded INI file. Typically you will make more changes. You can look at the
    <a href="#additionalinformation" use:scrollto={'#additionalinformation'}>additional information</a>
    at the end of this guide for more help on Project Zomboid server configuration.
  </p>
  <pre class="pre">PublicName=ZomBox demo server
ServerWelcomeMessage=Welcome to the ZomBox demo server.</pre>
</div>

<div class="content">
  <p><span class="step-title">46.</span>
    After making changes to the downloaded INI file. You can now upload it back to the server.
    Attach the INI file in Discord to upload it with the following command.
    Once again, the bot will react with a green tick emoji to show that the command was successful.
  </p>
  <pre class="pre">!setconfig ini</pre>
  <figure><img src="/instructions/46_setconfig_ini.png" alt="Set Config INI" /></figure>
</div>

<div class="content">
  <p><span class="step-title">47.</span>
    The server configuration has now been updated. However the server created a game world save (map)
    using the default configuration. You can delete the world with the following command.
  </p>
  <pre class="pre">!deployment wipe-world-save</pre>
  <figure><img src="/instructions/47_wipe_map.png" alt="Wipe Map" /></figure>
</div>

<div class="content">
  <p><span class="step-title">48.</span>
    Now start the server again. For this guide I used the local network IP to login to the Project Zomboid server.
    In order for other people to connect over the internet to your server, you need to redirect ports on your router.
    More information on that can be found in
    <a href="#additionalinformation" use:scrollto={'#additionalinformation'}>additional information</a>.
  </p>
  <p>
    After logging in I am greeted with the new Welcome Message I configured earlier.
    Also, if you set a Log Channel ID in the bot setup you should see a login event in that channel.
  </p>
  <pre class="pre">!server start</pre>
  <figure><img src="/instructions/48_login_server_details.png" alt="Login Server Details" /></figure>
  <figure><img src="/instructions/48_login_welcome_message.png" alt="Login Welcome Message" /></figure>
  <figure><img src="/instructions/48_login_event.png" alt="Login Event" /></figure>
</div>

<div class="content">
  <p><span class="step-title">48.</span>
    Try some server console commands now. Two examples shown below.
    You can broadcast a message to all players on the server.
    Items can also be spawned in a players inventory.
    See the help command for the full list of server console commands.
  </p>
  <pre class="pre">!world broadcast Hello Everyone</pre>
  <pre class="pre">!player Demo give-item Base Axe 2</pre>
  <figure><img src="/instructions/49_console_commands.png" alt="Console Commands" /></figure>
  <figure><img src="/instructions/49_world_broadcast.png" alt="World Broadcast" /></figure>
  <figure><img src="/instructions/49_give_item.png" alt="Give Item" /></figure>
</div>


<hr />
<div class="content" id="additionalinformation">
  <h2 class="title is-3">Additional Information</h2>
</div>

<div class="content">
  <h3 class="title is-4">Configuration Files</h3>
  <p>
    For help understanding Project Zomboid server configuration files. Please see the
    <a href="https://steamcommunity.com/sharedfiles/filedetails/?id=2682570605" target="_blank">excellent guide on Steam</a>
    by Aiteron.
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
  <h3 class="title is-4">Port Forwarding</h3>
  <p>
    In order for people to connect to your Project Zomboid server over the internet, your home
    router (internet gateway / "modem") needs to be configured to forward ports to the server.
    By default the server will automatically forward ports using UPnP. However, if this is not
    working on your LAN, you can manually add the port forwarding.
  </p>
  <p>
    To do this, login to your router then forward ports as shown below.
    Use of the IP address as shown on the ZomBox console. Note that the
    Players port range is for player connections, one port per player.
  </p>
  <table class="table">
    <thead>
      <tr><th>Purpose</th><th>Ports</th><th>Protocal</th></tr>
    </thead>
    <tbody class="is-family-monospace">
      <tr><td>Handshake</td><td>16261</td><td>UDP</td></tr>
      <tr><td>Players</td><td>16262-16294</td><td>TCP</td></tr>
      <tr><td>Steam</td><td>8766-8767</td><td>UDP</td></tr>
    </tbody>
  </table>
  <p>
    If using manual port forwarding you should also disable UPnP in the
    <span class="is-family-monospace">settings.ini</span> configuration file.
  </p>
  <pre class="pre"># Attempt to configure a UPnP-enabled internet gateway to automatically setup port forwarding rules. The server will fall back to default ports if this fails
UPnP=false</pre>
</div>

<div class="content">
  <h3 class="title is-4">Memory Allocations</h3>
  <p>
    ZomBox is a <a href="https://www.virtualbox.org" target="_blank">VirtualBox</a> virtual machine application.
    You can configure how much of your real machine memory and CPU the virtual machine is allowed to use.
    To do this click the <span class="has-text-weight-bold">Settings</span> cog button.
  </p>
  <figure><img src="/instructions/vb_main.png" alt="VirtualBox Main" /></figure>
  <p>
    Select the <span class="has-text-weight-bold">System</span> section on the left panel,
    then the <span class="has-text-weight-bold">Motherboard</span> tab.
    By default 9Gb of memory is allocated to ZomBox. This value should not be more
    than how much free memory your real machine has.
  </p>
  <figure><img src="/instructions/vb_sysmem.png" alt="ZomBox Memory" /></figure>
  <p>
    On the <span class="has-text-weight-bold">Processor</span> tab you can adjust how much CPU is allowed.
  </p>
  <figure><img src="/instructions/vb_syscpu.png" alt="ZomBox CPU" /></figure>
  <p>
    The Project Zomboid server that runs inside ZomBox also has a memory allocation.
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

<hr />


<style>
  .step-title {
    font-weight: bold;
    font-size: 1.2em;
  }

  .pre {
    margin: 0em 2.3em;
  }

  .table {
    margin: 0em 1.5em;
    width: 90%;
  }
</style>
