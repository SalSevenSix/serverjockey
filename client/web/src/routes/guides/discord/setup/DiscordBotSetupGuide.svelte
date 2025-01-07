<script>
  import { scrollto } from 'svelte-scrollto-next';
  import { surl } from '$lib/util/sjgmsapi';
  import Clyde from '$lib/svg/Clyde.svelte';
  import ExtLink from '$lib/widget/ExtLink.svelte';
  import BackToTop from '$lib/widget/BackToTop.svelte';
  import CodeBlock from '$lib/widget/CodeBlock.svelte';
  import ServerStatusStore from '$lib/instance/ServerStatusStore.svelte';
  import ServerStatus from '$lib/instance/ServerStatus.svelte';
  import ServerControls from '$lib/instance/ServerControls.svelte';
  import ServerLinkConfig from '$lib/svrlink/ServerLinkConfig.svelte';
</script>


<ServerStatusStore identity="serverlink">

<div class="columns">
  <div class="column is-one-quarter content mb-0">
    <figure class="image mt-2 max-200"><Clyde /></figure>
  </div>
  <div class="column is-three-quarters content">
    <h2 class="title is-3 mt-2">Discord Bot Setup</h2>
    <p>
      The Discord bot, also called
      <span class="has-text-weight-bold notranslate">ServerLink</span>,
      allows you to manage your servers as an alternative to the webapp.
      In order to use the bot you will need to register it on Discord. Just like a user account,
      the bot needs to be registered too. No coding is required, that is all in ServerJockey.
    </p>
    <p>
      If you are new to Discord
      <a href="#newDiscordAccount" use:scrollto={'#newDiscordAccount'}>start at step 1</a>
      to create an account for yourself. If you already have an account but need a Discord server,
      <a href="#newDiscordServer" use:scrollto={'#newDiscordServer'}>jump to step 2</a>.
      If you have a Discord server and just need the bot then
      <a href="#createBot" use:scrollto={'#createBot'}>jump to the create bot step</a>.
    </p>
  </div>
</div>

<div class="content" id="newDiscordAccount">
  <hr />
  <p><span class="step-title"></span>
    First step is to
    <ExtLink href="https://discord.com/login" wrap>login to Discord</ExtLink>
    in a browser. If you don&#39;t have an account then
    <ExtLink href="https://discord.com/register">register</ExtLink>
    a new one. Below is a screenshot of a fresh account for the guide called
    <span class="has-text-weight-bold notranslate">GuideUser</span>.
  </p>
  <figure class="image max-1024">
    <img src={surl('/assets/guides/discord/setup/new_account.png')}
         alt="New Discord Account" />
  </figure>
</div>

<div class="content" id="newDiscordServer">
  <p><span class="step-title"></span>
    Add a new Discord server by clicking the
    <span class="is-family-monospace is-size-5">+</span>
    button on the left panel.
  </p>
  <figure class="image max-1024">
    <img src={surl('/assets/guides/discord/setup/add_server_button.png')}
         alt="Add a Server" loading="lazy" />
  </figure>
</div>

<div class="content">
  <p><span class="step-title"></span>
    Select the
    <span class="has-text-weight-bold">Create My Own</span>
    option.
  </p>
  <figure class="image max-1024">
    <img src={surl('/assets/guides/discord/setup/create_server_options.png')}
         alt="Create Server Options" loading="lazy" />
  </figure>
</div>

<div class="content">
  <p><span class="step-title"></span>
    Choose the kind of Discord server you want, or skip to choose later.
  </p>
  <figure class="image max-1024">
    <img src={surl('/assets/guides/discord/setup/choose_server_type.png')}
         alt="Choose Server Type" loading="lazy" />
  </figure>
</div>

<div class="content">
  <p><span class="step-title"></span>
    Give your new Discord server a name. For the guide, I called it
    <span class="has-text-weight-bold notranslate">ServerJockeyGuide</span>.
  </p>
  <figure class="image max-1024">
    <img src={surl('/assets/guides/discord/setup/name_server.png')}
         alt="Name the Server" loading="lazy" />
  </figure>
</div>

<div class="content">
  <p><span class="step-title"></span>
    You should now have a new Discord server.
    Use the members button on the top right to toggle the member list panel on the right.
  </p>
  <figure class="image max-1024">
    <img src={surl('/assets/guides/discord/setup/fresh_server.png')}
         alt="Fresh Discord Server" loading="lazy" />
  </figure>
</div>

<div class="content" id="createBot">
  <p><span class="step-title"></span>
    With a Discord server ready to use, it&#39;s now time to setup the Discord bot. To begin, open the
    <ExtLink href="https://discord.com/developers" wrap>Discord Developer Portal</ExtLink>
    then click the
    <span class="has-text-weight-bold">New Application</span>
    button.
  </p>
  <figure class="image max-1028">
    <img src={surl('/assets/guides/discord/setup/developers_home.png')}
         alt="Discord Developer Portal" loading="lazy" />
  </figure>
</div>

<div class="content">
  <p><span class="step-title"></span>
    Give your application a name. For the guide, I called it
    <span class="has-text-weight-bold notranslate">ServerLink</span>.
  </p>
  <figure class="image max-1028">
    <img src={surl('/assets/guides/discord/setup/name_application.png')}
         alt="Name New App" loading="lazy" />
  </figure>
</div>

<div class="content">
  <p><span class="step-title"></span>
    You should now have a new Discord application. It should look like the screenshot below.
  </p>
  <figure class="image max-1028">
    <img src={surl('/assets/guides/discord/setup/fresh_application.png')}
         alt="Fresh App" loading="lazy" />
  </figure>
</div>

<div class="content">
  <p><span class="step-title"></span>
    On the left panel, select the
    <span class="has-text-weight-bold">Installation</span>
    section. Change the
    <span class="has-text-weight-bold">Install Link</span>
    to be
    <span class="has-text-weight-bold">None</span>
    in the dropdown. Then click
    <span class="has-text-weight-bold">Save Changes</span>
    button.
  </p>
  <figure class="image max-1028">
    <img src={surl('/assets/guides/discord/setup/install_link_none.png')}
         alt="Install Link None" loading="lazy" />
  </figure>
</div>

<div class="content">
  <p><span class="step-title"></span>
    Now select the
    <span class="has-text-weight-bold">Bot</span>
    section to configure the bot.
  </p>
  <figure class="image max-1028">
    <img src={surl('/assets/guides/discord/setup/fresh_bot.png')}
         alt="Fresh Bot" loading="lazy" />
  </figure>
</div>

<div class="content">
  <p><span class="step-title"></span>
    Scroll down the bot settings to find the
    <span class="has-text-weight-bold">PUBLIC BOT</span>
    switch and turn it OFF. Scroll down further to find the
    <span class="has-text-weight-bold">MESSAGE CONTENT INTENT</span>
    switch and turn it ON. Then click
    <span class="has-text-weight-bold">Save Changes</span>
    button.
  </p>
  <figure class="image max-1028">
    <img src={surl('/assets/guides/discord/setup/make_bot_private.png')}
         alt="Make Bot Private" loading="lazy" />
  </figure>
  <figure class="image max-1028">
    <img src={surl('/assets/guides/discord/setup/allow_receive_messages.png')}
         alt="Allow Receive Messages" loading="lazy" />
  </figure>
</div>

<div class="content">
  <p><span class="step-title"></span>
    With the new bot created, it&#39;s time to invite the bot to your Discord server.
    On the left panel, select the
    <span class="has-text-weight-bold">OAuth2</span>
    section. Now on the right panel in
    <span class="has-text-weight-bold">SCOPES</span>,
    check the
    <span class="has-text-weight-bold">bot</span>
    checkbox.
  </p>
  <figure class="image max-1028">
    <img src={surl('/assets/guides/discord/setup/bot_invite_scope.png')}
         alt="Choose Bot Scope" loading="lazy" />
  </figure>
</div>

<div class="content">
  <p><span class="step-title"></span>
    Scroll down to
    <span class="has-text-weight-bold">BOT PERMISSIONS</span>,
    then check all the checkboxes as shown in the screenshot below. Then click the
    <span class="has-text-weight-bold">Copy</span>
    button to copy the generated invite URL.
  </p>
  <figure class="image max-850">
    <img src={surl('/assets/guides/discord/setup/bot_invite_perms.png')}
         alt="Choose Bot Perms" loading="lazy" />
  </figure>
</div>

<div class="content">
  <p><span class="step-title"></span>
    Open a new tab in the browser. Paste the URL into the address bar then hit Enter key.
  </p>
  <figure class="image max-1024">
    <img src={surl('/assets/guides/discord/setup/bot_invite_url.png')}
         alt="Invite Bot" loading="lazy" />
  </figure>
</div>

<div class="content">
  <p><span class="step-title"></span>
    Choose your Discord server from the
    <span class="has-text-weight-bold">ADD TO SERVER</span>
    dropdown list, then click the
    <span class="has-text-weight-bold">Continue</span>
    button.
  </p>
  <figure class="image max-1024">
    <img src={surl('/assets/guides/discord/setup/bot_invite_choose_server.png')}
         alt="Choose Server for Bot" loading="lazy" />
  </figure>
</div>

<div class="content">
  <p><span class="step-title"></span>
    Click the
    <span class="has-text-weight-bold">Authorize</span>
    button to complete the bot invite.
  </p>
  <figure class="image max-1024">
    <img src={surl('/assets/guides/discord/setup/bot_invite_authorize.png')}
         alt="Authorise Bot" loading="lazy" />
  </figure>
</div>

<div class="content">
  <p><span class="step-title"></span>
    Your new bot has now joined your Discord server!
  </p>
  <figure class="image max-1024">
    <img src={surl('/assets/guides/discord/setup/bot_invite_authorized.png')}
         alt="Bot Authorised" loading="lazy" />
  </figure>
</div>

<div class="content">
  <p><span class="step-title"></span>
    Now go to the Discord server browser tab.
    You should now see the bot as a member on the right panel.
    It will be offline, that is expected.
  </p>
  <figure class="image max-1024">
    <img src={surl('/assets/guides/discord/setup/bot_invite_fresh.png')}
         alt="Bot Invited" loading="lazy" />
  </figure>
</div>

<div class="content">
  <p><span class="step-title"></span>
    Before starting the bot, it&#39;s recommended that you enable the developer features in Discord.
    This will allow you to see the channel IDs. If already enabled or you don&#39;t want to do this then skip to the
    <a href="#getBotToken" use:scrollto={'#getBotToken'}>bot login token</a>
    step.
  </p>
  <p>
    To enable, open
    <span class="has-text-weight-bold">User Settings</span>
    with the cog button.
  </p>
  <figure class="image max-1024">
    <img src={surl('/assets/guides/discord/setup/open_settings.png')}
         alt="Open Discord Settings" loading="lazy" />
  </figure>
</div>

<div class="content">
  <p><span class="step-title"></span>
    Select the
    <span class="has-text-weight-bold">Advanced</span>
    section in the left panel. Then switch on
    <span class="has-text-weight-bold">Developer Mode</span>.
    Now click the
    <span class="has-text-weight-bold">ESC</span>
    button at the top right to close Settings.
  </p>
  <figure class="image max-1024">
    <img src={surl('/assets/guides/discord/setup/enable_developer_mode.png')}
         alt="Enable Developer Mode" loading="lazy" />
  </figure>
</div>

<div class="content">
  <p><span class="step-title"></span>
    With Developer Mode enabled. If you right-click on a Channel, there is now a menu option to
    <span class="has-text-weight-bold">Copy Channel ID</span>.
    This will be useful later on.
  </p>
  <figure class="image max-1024">
    <img src={surl('/assets/guides/discord/setup/copy_channel_id.png')}
         alt="Copy Channel ID" loading="lazy" />
  </figure>
</div>

<div class="content" id="getBotToken">
  <p><span class="step-title"></span>
    Time to startup the bot. First a login token is needed. Go to the Developer Portal browser tab again. In the
    <span class="has-text-weight-bold">Bot</span>
    section click the
    <span class="has-text-weight-bold">Reset Token</span>
    button. This will generate a new token.
  </p>
  <figure class="image max-1028">
    <img src={surl('/assets/guides/discord/setup/reset_bot_token.png')}
         alt="Reset Bot Token" loading="lazy" />
  </figure>
</div>

<div class="content">
  <p><span class="step-title"></span>
    Click the
    <span class="has-text-weight-bold">Yes, do it!</span>
    button to confirm.
  </p>
  <figure class="image max-1028">
    <img src={surl('/assets/guides/discord/setup/accept_reset_bot_token.png')}
         alt="Accept Reset Bot Token" loading="lazy" />
  </figure>
</div>

<div class="content">
  <p><span class="step-title"></span>
    Now click the
    <span class="has-text-weight-bold">Copy</span>
    button to copy the new token.
  </p>
  <figure class="image max-1028">
    <img src={surl('/assets/guides/discord/setup/copy_bot_token.png')}
         alt="Copy Bot Token" loading="lazy" />
  </figure>
</div>

<div class="content">
  <p><span class="step-title"></span>
    Paste the token into the
    <span class="has-text-weight-bold">Discord Bot Token</span>
    field in the form below. Optionally copy and paste a channel ID into the
    <span class="has-text-weight-bold">Channel ID</span>
    fields. Then click the
    <span class="has-text-weight-bold">Save</span>
    button to save changes.
  </p>
</div>
<div class="columns is-mobile is-centered">
  <div class="column is-11">
    <div class="box">
      <ServerLinkConfig noHints />
    </div>
  </div>
</div>

<div class="content">
  <p><span class="step-title"></span>
    Finally time to start the bot! Click the
    <span class="has-text-weight-bold">Start</span>
    button below.
  </p>
</div>
<div class="columns is-mobile is-centered">
  <div class="column is-11">
    <div class="box">
      <ServerStatus stateOnly />
      <ServerControls />
    </div>
  </div>
</div>

<div class="content">
  <p><span class="step-title"></span>
    Go to the Discord server browser tab again. You should now see the bot online on the right panel.
    Congratulations making it this far! Note that the Discord bot configuration and controls can be found
    on the home page of this webapp. No need to come back here to make changes or start &amp; stop the bot.
  </p>
  <figure class="image max-1024">
    <img src={surl('/assets/guides/discord/setup/bot_logged_in.png')}
         alt="Bot Logged In" loading="lazy" />
  </figure>
</div>

<div class="content">
  <p><span class="step-title"></span>
    Now try out the bot, it will work on any channel it has access to.
    First try the help command as shown below. The bot should reply with available commands.
  </p>
  <CodeBlock>!help</CodeBlock>
  <figure class="image max-800">
    <img src={surl('/assets/guides/discord/setup/help_system.png')}
         alt="System Help" loading="lazy" />
  </figure>
</div>

<div class="content">
  <p><span class="step-title"></span>
    Now try creating an instance as shown below. The bot reacts with a lock emoji which means it didn&#39;t work!
    This is expected, you aren&#39;t authorised to create an instance yet. Next steps will remedy this.
  </p>
  <CodeBlock>!create myserver projectzomboid</CodeBlock>
  <figure class="image max-800">
    <img src={surl('/assets/guides/discord/setup/create_instance_locked.png')}
         alt="Create Instances Locked" loading="lazy" />
  </figure>
</div>

<div class="content">
  <p><span class="step-title"></span>
    Right click on your Discord server in the left panel. Find
    <span class="has-text-weight-bold">Server Settings</span>
    then click on
    <span class="has-text-weight-bold">Roles</span>.
  </p>
  <figure class="image max-1024">
    <img src={surl('/assets/guides/discord/setup/open_roles.png')}
         alt="Open Roles" loading="lazy" />
  </figure>
</div>

<div class="content">
  <p><span class="step-title"></span>
    Click the
    <span class="has-text-weight-bold">Create Role</span>
    button.
  </p>
  <figure class="image max-1024">
    <img src={surl('/assets/guides/discord/setup/create_role_new.png')}
         alt="Create New Role" loading="lazy" />
  </figure>
</div>

<div class="content">
  <p><span class="step-title"></span>
    Enter role name
    <span class="has-text-weight-bold notranslate">admin</span>
    as specified in Admin Roles in the bot configuration. Then click
    <span class="has-text-weight-bold">Save Changes</span>
    button.
  </p>
  <figure class="image max-1024">
    <img src={surl('/assets/guides/discord/setup/create_admin_role.png')}
         alt="Create Admin Role" loading="lazy" />
  </figure>
</div>

<div class="content">
  <p><span class="step-title"></span>
    Select the
    <span class="has-text-weight-bold">Manage Members</span>
    tab. Then click the
    <span class="has-text-weight-bold">Add Members</span>
    button.
  </p>
  <figure class="image max-1024">
    <img src={surl('/assets/guides/discord/setup/add_member.png')}
         alt="Add Members to Role" loading="lazy" />
  </figure>
</div>

<div class="content">
  <p><span class="step-title"></span>
    Add yourself and any other members on your Discord server that you want to grant access to manage servers. Click
    <span class="has-text-weight-bold">Add</span>
    button then the
    <span class="has-text-weight-bold">ESC</span>
    button at the top right to close Settings.
  </p>
  <figure class="image max-1024">
    <img src={surl('/assets/guides/discord/setup/choose_member.png')}
         alt="Choose Members for Role" loading="lazy" />
  </figure>
</div>

<div class="content">
  <p><span class="step-title"></span>
    Now try creating an instance again. For the guide the instance is called
    <span class="has-text-weight-bold notranslate">myserver</span>.
    The name must be lower case letters and numbers, no spaces or special characters except dashes and underscores.
    The second value is
    <span class="has-text-weight-bold notranslate">projectzomboid</span>.
    This is the module, which is a supported game server. So this instance will be for a Project Zomboid server.
  </p>
  <CodeBlock>!create myserver projectzomboid</CodeBlock>
  <figure class="image max-800">
    <img src={surl('/assets/guides/discord/setup/create_instance_success.png')}
         alt="Create Instances Success" loading="lazy" />
  </figure>
</div>

<div class="content">
  <hr />
  <h4 class="title is-5">So what next?</h4>
  <p>
    The Discord bot is setup and working! So that is the end of this guide.
    However if you want to learn how to use the bot to setup, configure and start a game server.
    Go to the <a href={surl('/guides/discord/usage')}>Discord bot usage guide</a>.
  </p>
</div>

</ServerStatusStore>
<BackToTop />


<style>
  figure.max-850 img {
    max-width: 850px;
  }

  figure.max-1028 img {
    max-width: 1028px;
  }
</style>
