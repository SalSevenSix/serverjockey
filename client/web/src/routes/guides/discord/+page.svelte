<script>
  import { scrollto } from 'svelte-scrollto-element';
  import { baseurl, instance } from '$lib/sjgmsapi';
  import BackToTop from '$lib/BackToTop.svelte';
  import ServerStatusStore from '$lib/ServerStatusStore.svelte';
  import ServerStatus from '$lib/ServerStatus.svelte';
  import ServerControls from '$lib/ServerControls.svelte';
  import ServerLinkConfig from '$lib/ServerLinkConfig.svelte';

  // used by ServerStatusStore
  instance.set({ url: baseurl + '/instances/serverlink' });
</script>


<div class="content">
  <h2 class="title is-3 mt-2">Discord Bot Setup</h2>
  <p>
    The Discord bot, also called <span class="has-text-weight-bold">ServerLink</span>,
    allows you to manage your servers as an alternative to the webapp.
    Most features are supported, with a few extra unique features as well.
    In order to use the bot you will need to register it on Discord. No coding is required,
    that is all in ServerJockey. Just like a user account, the bot needs to be registered.
  </p>
  <p>
    If you are new to Discord
    <a href="#newDiscordAccount" use:scrollto={'#newDiscordAccount'}>start at step 1</a>
    to create an account for yourself.
    If you already have an account but need a Discord server,
    <a href="#newDiscordServer" use:scrollto={'#newDiscordServer'}>jump to step 2</a>.
    If you have a Discord server and just need the bot then
    <a href="#createBot" use:scrollto={'#createBot'}>jump to the create bot step</a>.
  </p>
</div>

<div class="content" id="newDiscordAccount">
  <hr />
  <p><span class="step-title">01.</span>
    First step is to <a href="https://discord.com/login" target="_blank">
    login to Discord <i class="fa fa-up-right-from-square"></i></a> in your browser.
    If you don&#39;t have an account then <a href="https://discord.com/register" target="_blank">
    register <i class="fa fa-up-right-from-square"></i></a> a new one.
    Below is screenshot of a fresh account for the guide.
  </p>
  <figure><img src="/assets/setup/01_new_account.png" alt="New Discord Account" /></figure>
</div>

<div class="content" id="newDiscordServer">
  <p><span class="step-title">02.</span>
    Add a new Discord server by clicking the <span class="is-family-monospace is-size-5">+</span> button
    on the left panel.
  </p>
  <figure><img src="/assets/setup/02_add_server_button.png" alt="Add a Server" /></figure>
</div>

<div class="content">
  <p><span class="step-title">03.</span>
    Select the <span class="has-text-weight-bold">Create My Own</span> option.
  </p>
  <figure><img src="/assets/setup/03_create_server_options.png" alt="Create Server Options" /></figure>
</div>

<div class="content">
  <p><span class="step-title">04.</span>
    Choose the kind of Discord server you want, or skip to choose later.
  </p>
  <figure><img src="/assets/setup/04_choose_server_type.png" alt="Choose Server Type" /></figure>
</div>

<div class="content">
  <p><span class="step-title">05.</span>
    Give your new Discord server a name. Can be anything that Discord allows.
  </p>
  <figure><img src="/assets/setup/05_name_server.png" alt="Name the Server" /></figure>
</div>

<div class="content">
  <p><span class="step-title">06.</span>
    You should now have a new Discord server. It should look like the screenshot below.
    For the guide, I called the server ZomBoxGuide.
  </p>
  <figure><img src="/assets/setup/06_fresh_server.png" alt="Fresh Discord Server" /></figure>
</div>

<div class="content" id="createBot">
  <p><span class="step-title">07.</span>
    Now that a new or existing Discord server is ready. It is time to create a Discord bot.
    Don&#39;t worry! No coding is required, that is all in ServerJockey. This is the bot setup on Discord.
    Similar to how users register an account to login, bots also need to be registered to login.
  </p>
  <p>
    To begin the setup process.
    Open the <a href="https://discord.com/developers" target="_blank">
    Discord Developer Portal <i class="fa fa-up-right-from-square"></i></a>
    then click the <span class="has-text-weight-bold">New Application</span> button.
  </p>
  <figure><img src="/assets/setup/07_developers_home.png" alt="Discord Developer Portal" /></figure>
</div>

<div class="content">
  <p><span class="step-title">08.</span>
    Give your application a name. It can be anything that Discord allows.
    For the guide, I called it zombox-demo.
  </p>
  <figure><img src="/assets/setup/08_name_application.png" alt="Name New App" /></figure>
</div>

<div class="content">
  <p><span class="step-title">09.</span>
    You should now have a new Discord application. It should look like the screenshot below.
  </p>
  <figure><img src="/assets/setup/09_fresh_application.png" alt="Fresh App" /></figure>
</div>

<div class="content">
  <p><span class="step-title">10.</span>
    In the <span class="has-text-weight-bold">SETTINGS</span> on the left panel,
    select the <span class="has-text-weight-bold">Bot</span> section.
    Then click the <span class="has-text-weight-bold">Add Bot</span> button.
  </p>
  <figure><img src="/assets/setup/10_add_bot.png" alt="Add a Bot" /></figure>
</div>

<div class="content">
  <p><span class="step-title">11.</span>
    Click the <span class="has-text-weight-bold">Yes, do it!</span> button to confirm adding the bot to the application.
  </p>
  <figure><img src="/assets/setup/11_accept_new_bot.png" alt="Accept New Bot" /></figure>
</div>

<div class="content">
  <p><span class="step-title">12.</span>
     You should now have a new Discord bot. It should look like the screenshot below.
  </p>
  <figure><img src="/assets/setup/12_fresh_bot.png" alt="Fresh Bot" /></figure>
</div>

<div class="content">
  <p><span class="step-title">13.</span>
    Scroll down the bot settings to find the <span class="has-text-weight-bold">PUBLIC BOT</span>
    switch and turn it OFF.
    Scroll down further to find the <span class="has-text-weight-bold">MESSAGE CONTENT INTENT</span>
    switch and turn it ON.
    Then click <span class="has-text-weight-bold">Save Changes</span> button.
  </p>
  <figure><img src="/assets/setup/13_make_bot_private.png" alt="Make Bot Private" /></figure>
  <figure><img src="/assets/setup/13_allow_receive_messages.png" alt="Allow Receive Messages" /></figure>
</div>

<div class="content">
  <p><span class="step-title">14.</span>
    With the new bot created, it&#39;s time to invite the bot to your Discord server.
    In the <span class="has-text-weight-bold">SETTINGS</span> on the left panel,
    select the <span class="has-text-weight-bold">OAuth2</span> section.
    Then select the <span class="has-text-weight-bold">URL Generator</span> under that.
    Now on the right panel, in <span class="has-text-weight-bold">SCOPES</span>,
    check the <span class="has-text-weight-bold">bot</span> checkbox.
  </p>
  <figure><img src="/assets/setup/14_bot_invite_scope.png" alt="Set Bot Scope" /></figure>
</div>

<div class="content">
  <p><span class="step-title">15.</span>
    Scroll down to <span class="has-text-weight-bold">BOT PERMISSIONS</span>.
    Then check all the checkboxes as shown in the screenshot below.
    Now click the <span class="has-text-weight-bold">Copy</span> button
    to copy the generated invite URL.
  </p>
  <figure><img src="/assets/setup/15_bot_invite_perms.png" alt="Set Bot Perms" /></figure>
</div>

<div class="content">
  <p><span class="step-title">16.</span>
    Open a new tab in your browser. Paste the URL into the address bar then hit enter.
  </p>
  <figure><img src="/assets/setup/16_bot_invite_url.png" alt="Invite Bot" /></figure>
</div>

<div class="content">
  <p><span class="step-title">17.</span>
    Choose your Discord server from the <span class="has-text-weight-bold">ADD TO SERVER</span> dropdown list.
    Then click the <span class="has-text-weight-bold">Continue</span> button.
  </p>
  <figure><img src="/assets/setup/17_bot_invite_choose_server.png" alt="Choose Server for Bot" /></figure>
</div>

<div class="content">
  <p><span class="step-title">18.</span>
    Click the <span class="has-text-weight-bold">Authorize</span> button to complete the bot invite.
  </p>
  <figure><img src="/assets/setup/18_bot_invite_authorize.png" alt="Authorise Bot" /></figure>
</div>

<div class="content">
  <p><span class="step-title">19.</span>
    Your new bot has now joined your Discord server!
  </p>
  <figure><img src="/assets/setup/19_bot_invite_authorized.png" alt="Bot Authorised" /></figure>
</div>

<div class="content">
  <p><span class="step-title">20.</span>
    Now go to the Discord server browser tab. You should now see the bot as a member on the right panel.
    It will be offline, that is expected. If you do not see the member panel on the right,
    hit the people button. It&#39;s just to the left of Search.
  </p>
  <figure><img src="/assets/setup/20_bot_invite_fresh.png" alt="Bot Invited" /></figure>
</div>

<div class="content">
  <p><span class="step-title">21.</span>
    Before starting up the bot, it is recommended that you enable the developer features in Discord.
    This will allow you to see the channel IDs. If already enabled or you don&#39;t want to do this then
    skip to the <a href="#getBotToken" use:scrollto={'#getBotToken'}>bot login token</a> step.
  </p>
  <p>
    To enable, open <span class="has-text-weight-bold">User Settings</span> with the cog button.
  </p>
  <figure><img src="/assets/setup/21_open_settings.png" alt="Open Discord Settings" /></figure>
</div>

<div class="content">
  <p><span class="step-title">22.</span>
    Select the <span class="has-text-weight-bold">Advanced</span> section in the left panel.
    Then switch on <span class="has-text-weight-bold">Developer Mode</span>.
    Now click the <span class="has-text-weight-bold">ESC</span> button at the top right to close Settings.
  </p>
  <figure><img src="/assets/setup/22_enable_developer_mode.png" alt="Enable Developer Mode" /></figure>
</div>

<div class="content">
  <p><span class="step-title">23.</span>
    With Developer Mode enabled. If you right-click on a Channel, there is now a menu option to
    <span class="has-text-weight-bold">Copy ID</span>. This will be useful later on.
  </p>
  <figure><img src="/assets/setup/23_copy_channel_id.png" alt="Copy Channel ID" /></figure>
</div>

<div class="content" id="getBotToken">
  <p><span class="step-title">24.</span>
    Time to startup the bot. First a login token is needed. Go to the Developer Portal browser tab again.
    In the <span class="has-text-weight-bold">Bot</span> section click
    the <span class="has-text-weight-bold">Reset Token</span> button.
    This will reset and generate a new token.
  </p>
  <figure><img src="/assets/setup/24_reset_bot_token.png" alt="Reset Bot Token" /></figure>
</div>

<div class="content">
  <p><span class="step-title">25.</span>
    Click the <span class="has-text-weight-bold">Yes, do it!</span> button to confirm.
  </p>
  <figure><img src="/assets/setup/25_accept_reset_bot_token.png" alt="Accept Reset Bot Token" /></figure>
</div>

<div class="content">
  <p><span class="step-title">26.</span>
    Now click the <span class="has-text-weight-bold">Copy</span> button to copy the new token.
  </p>
  <figure><img src="/assets/setup/26_copy_bot_token.png" alt="Copy Bot Token" /></figure>
</div>

<div class="content">
  <p><span class="step-title">27.</span>
    Paste the token into the <span class="has-text-weight-bold">Discord Bot Token</span> field in the form below.
    Optionally copy and paste a Channel ID into the <span class="has-text-weight-bold">Log Channel ID</span> field.
    Then click the <span class="has-text-weight-bold">Save</span> button to save changes.
  </p>
</div>
<hr />
<div class="columns is-mobile is-centered">
  <div class="column is-11">
    <ServerLinkConfig noHints />
  </div>
</div>
<hr />

<div class="content">
  <p><span class="step-title">28.</span>
    Finally time to start the bot. Don&#39;t worry if you first see an error below.
    The bot failed to login when you started ServerJockey for the first time because no login token was set.
    It is now, so click the <span class="has-text-weight-bold">Start</span> button.
  </p>
</div>
<hr />
<div class="columns is-mobile is-centered">
  <div class="column is-11">
    <ServerStatusStore>
      <ServerStatus stateOnly />
      <ServerControls />
    </ServerStatusStore>
  </div>
</div>
<hr />

<div class="content">
  <p><span class="step-title">29.</span>
    Go to the Discord server browser tab again. You should now see the bot online on the right panel.
    Congratulations making it this far! Note that the Discord bot config and controls can be found on the
    home page of this webapp. No need to come back here to make config changes or stop &amp; start the bot.
  </p>
  <figure><img src="/assets/setup/29_bot_logged_in.png" alt="Bot Logged In" /></figure>
</div>

<div class="content">
  <p><span class="step-title">30.</span>
    Now it&#39;s time to try out the bot. The bot will work from any channel it has access to.
    First try the help command as shown below. The bot should reply with available commands.
  </p>
  <pre class="pre is-thinner">!help</pre>
  <figure><img src="/assets/setup/30_help_system.png" alt="System Help" /></figure>
</div>

<div class="content">
  <p><span class="step-title">31.</span>
    Now try the instances command. An instance is a game server container. This command will list them all.
    The response shows none are found because no instance has been created yet.
  </p>
  <pre class="pre is-thinner">!instances</pre>
  <figure><img src="/assets/setup/31_instances_empty.png" alt="Instances Empty" /></figure>
</div>

<div class="content">
  <p><span class="step-title">32.</span>
    Now try creating an instance as shown below. The bot reacts with a lock emoji which means it didn&#39;t work!
    This is expected, you aren&#39;t authorised to create an instance yet. Next steps will remedy this.
  </p>
  <pre class="pre is-thinner">!create myserver projectzomboid</pre>
  <figure><img src="/assets/setup/32_create_instance_locked.png" alt="Create Instances Locked" /></figure>
</div>

<div class="content">
  <p><span class="step-title">33.</span>
    Right click on your Discord server in the left panel.
    Find <span class="has-text-weight-bold">Server Settings</span>
    then click on <span class="has-text-weight-bold">Roles</span>.
  </p>
  <figure><img src="/assets/setup/33_open_roles.png" alt="Open Roles" /></figure>
</div>

<div class="content">
  <p><span class="step-title">34.</span>
    Click the <span class="has-text-weight-bold">Create Role</span> button.
  </p>
  <figure><img src="/assets/setup/34_create_role_new.png" alt="Create New Role" /></figure>
</div>

<div class="content">
  <p><span class="step-title">35.</span>
    Enter a role name of <span class="is-family-monospace">pzadmin</span> as specified
    in the <span class="has-text-weight-bold">Admin Role</span> in the bot config.
    Now <span class="has-text-weight-bold">Save Changes</span>
    then select the <span class="has-text-weight-bold">Manage Members</span> tab.
  </p>
  <figure><img src="/assets/setup/35_create_pzadmin_role.png" alt="Create PZAdmin Role" /></figure>
</div>

<div class="content">
  <p><span class="step-title">36.</span>
    Click the <span class="has-text-weight-bold">Add Members</span> button.
  </p>
  <figure><img src="/assets/setup/36_add_member.png" alt="Add Members to Role" /></figure>
</div>

<div class="content">
  <p><span class="step-title">37.</span>
    Add yourself and any other members on your Discord server that you want access to manage
    your game servers. Then click <span class="has-text-weight-bold">Add</span> button.
    Optionally you can select the <span class="has-text-weight-bold">Permissions</span> tab
    and make changes as you want. When done click the <span class="has-text-weight-bold">ESC</span>
    button at the top right to close Settings.
  </p>
  <figure><img src="/assets/setup/37_choose_member.png" alt="Choose Members for Role" /></figure>
</div>

<div class="content">
  <p><span class="step-title">38.</span>
    Now try creating an instance again. For this guide I called the instance
    <span class="has-text-weight-bold">myserver</span>. You can give your instance a different name,
    but it must be lower case characters, numbers, dashes, underscores, no other special characters.
    The second command value is <span class="has-text-weight-bold">projectzomboid</span>.
    This is the module name, which is a supported game server. In this case, Project Zomboid.
    So this instance will be for a Project Zomboid server.
  </p>
  <pre class="pre is-thinner">!create myserver projectzomboid</pre>
  <figure><img src="/assets/setup/38_create_instance_success.png" alt="Create Instances Success" /></figure>
  <p>
    After creation, you can try the instances command again to see the new instance.
    The arrow will mark the current selected instance.
  </p>
  <pre class="pre is-thinner">!instances</pre>
  <figure><img src="/assets/setup/38_list_new_instance.png" alt="View New Instance" /></figure>
</div>

<div class="content">
  <hr />
  <p><span class="step-title">So what next?</span></p>
  <p>
    The Discord bot is setup and working! So this is the end of this guide. However if you wish to continue
    setting up and starting a Project Zomboid server using the bot, go to the
    <a href="/guides/servers/projectzomboid">Project Zomboid guide</a>.
  </p>
</div>

<BackToTop />
