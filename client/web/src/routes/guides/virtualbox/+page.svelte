<script>
  import { scrollto } from 'svelte-scrollto-next';
  import { surl } from '$lib/util/sjgmsapi';
  import BackToTop from '$lib/widget/BackToTop.svelte';
  import ExtLink from '$lib/widget/ExtLink.svelte';
  import CodeBlock from '$lib/widget/CodeBlock.svelte';
</script>


<div class="columns">
  <div class="column is-one-quarter content mb-0 pb-0">
    <figure class="image mr-0 max-300">
      <img src={surl('/assets/brands/Virtualbox_logo.png')} alt="Virtualbox logo" />
    </figure>
  </div>
  <div class="column is-three-quarters content">
    <h2 class="title is-3 mt-2 notranslate">VirtualBox</h2>
    <p>
      <ExtLink href="https://www.virtualbox.org" notranslate>VirtualBox</ExtLink>
      is a free virtualization system for enterprise and personal use. It allows you to run a virtual machine
      on a real machine. ServerJockey is available as a VirtualBox Appliance (virtual machine image).
      The appliance is running Ubuntu Server OS with ServerJockey pre-installed and ready to use.
    </p>
    <p>
      This guide provides information on how to configure, use and care for the appliance.
      For comprehensive information about VirtualBox, consult the
      <ExtLink href="https://www.virtualbox.org/manual/UserManual.html">online manual</ExtLink>
    </p>
    <ul>
      <li><a href="#vbsettings" use:scrollto={'#vbsettings'}>Memory and Processor Settings</a></li>
      <li><a href="#sshutdown" use:scrollto={'#sshutdown'}>Safe Shutdown</a></li>
      <li><a href="#howtologin" use:scrollto={'#howtologin'}>Login to OS</a></li>
      <li><a href="#changepwd" use:scrollto={'#changepwd'}>Change Password</a></li>
      <li><a href="#updateos" use:scrollto={'#updateos'}>Update OS</a></li>
      <li><a href="#enablessh" use:scrollto={'#enablessh'}>Remote access using SSH</a></li>
      <li><a href="#enablesamba" use:scrollto={'#enablesamba'}>Remote access using File Sharing</a></li>
    </ul>
  </div>
</div>

<div class="content">
  <hr />
  <h3 id="vbsettings" class="title is-4">Memory and Processor Settings</h3>
  <p>
    You can configure how much of your real machine Memory and Processor the appliance is allowed to use.
    To do this click the
    <span class="has-text-weight-bold">Settings</span>
    cog button.
  </p>
  <figure class="image max-800">
    <img src={surl('/assets/guides/virtualbox/main.png')} alt="VirtualBox Settings" />
  </figure>
  <p>
    Select the
    <span class="has-text-weight-bold">System</span>
    section on the left panel, then the
    <span class="has-text-weight-bold">Motherboard</span>
    tab. The ServerJockey appliance has 10Gb of memory allocated.
    You can change this value as needed. It should less than how much free memory your real machine has,
    but enough to support the game server you are running with 2Gb spare.
  </p>
  <figure class="image max-800">
    <img src={surl('/assets/guides/virtualbox/sysmem.png')} alt="VirtualBox Memory" loading="lazy" />
  </figure>
  <p>
    On the
    <span class="has-text-weight-bold">Processor</span>
    tab you can adjust how much processor is allocated.
    You can specify a number of cores as well as an execution cap. Click
    <span class="has-text-weight-bold">OK</span>
    to save changes.
  </p>
  <figure class="image max-800">
    <img src={surl('/assets/guides/virtualbox/syscpu.png')} alt="VirtualBox Processor" loading="lazy" />
  </figure>

  <h3 id="sshutdown" class="title is-4">Safe Shutdown</h3>
  <p>
    To safely shutdown the appliance use the
    <span class="has-text-weight-bold">ACPI Shutdown</span>
    option under
    <span class="has-text-weight-bold">Machine</span>
    in the menu.
  </p>
  <figure class="image max-400">
    <img src={surl('/assets/guides/virtualbox/shutdown.png')} alt="Safe Shutdown" loading="lazy" />
  </figure>

  <h3 id="howtologin" class="title is-4">Login to OS</h3>
  <p>
    The appliance is running Ubuntu Server OS. You can login to the command line console if needed. Hit the
    <span class="has-text-weight-bold">Enter</span>
    key to show the login prompt. Login with user
    <span class="is-family-monospace notranslate">zombox</span>
    and password
    <span class="is-family-monospace notranslate">zombox</span>.
    Remote access is disabled so this default password is acceptable for initial use.
  </p>
  <figure class="image max-800">
    <img src={surl('/assets/guides/virtualbox/login.png')} alt="Console Login prompt" loading="lazy" />
  </figure>

  <h3 id="changepwd" class="title is-4">Change Password</h3>
  <p>
    It&#39;s recommended you change the default password,
    <span class="is-italic">especially</span>
    when enabling remote access. Use the following command to change the password.
  </p>
  <CodeBlock>passwd</CodeBlock>
  <figure class="image max-400">
    <img src={surl('/assets/guides/virtualbox/changepwd.png')} alt="Change Password" loading="lazy" />
  </figure>

  <h3 id="updateos" class="title is-4">Update OS</h3>
  <p>
    It&#39;s recommended you periodically update the Ubuntu Server OS and restart the appliance.
    Use the following commands to do this.
  </p>
  <CodeBlock>sudo apt update</CodeBlock>
  <CodeBlock>sudo apt upgrade</CodeBlock>
  <CodeBlock>sudo reboot</CodeBlock>

  <h3 id="enablessh" class="title is-4 pt-2">Remote access using SSH</h3>
  <p>
    By default remote access using SSH is disabled for security reasons. If you wish to login remotely
    you can turn on SSH with the command shown below. If you want to login remotely from a Windows machine,
    <ExtLink href="https://apps.microsoft.com/detail/xpfnzksklbp7rj" notranslate>PuTTY</ExtLink>
    is a popular SSH client.
  </p>
  <CodeBlock>sudo systemctl start ssh</CodeBlock>
  <p>
    Enable the SSH service to automatically start SSH when the appliance starts.
  </p>
  <CodeBlock>sudo systemctl enable ssh</CodeBlock>

  <h3 id="enablesamba" class="title is-4 pt-2">Remote access using File Sharing</h3>
  <p>
    By default File Sharing is disabled for security reasons. If you wish to remotely access
    the filesystem with sharing, you can turn on Samba with the command shown below.
  </p>
  <CodeBlock>sudo systemctl start smbd</CodeBlock>
  <p>
    Enable the Samba service to automatically start Samba when the appliance starts.
  </p>
  <CodeBlock>sudo systemctl enable smbd</CodeBlock>
  <p>
    On Windows, you can find the appliance in the Network section of Windows File Explorer,
    but don&#39;t expect Windows to discover it. Instead, enter the
    <span class="has-text-weight-bold">Local IP</span>
    of the appliance starting with two backslashes in the address bar then hit
    <span class="has-text-weight-bold">Enter</span>.
    A folder called
    <span class="has-text-weight-bold">zombox</span>
    should be visible to browse and mount as a drive.<br />
    <span class="has-text-weight-bold">e.g.</span>&nbsp; <span class="is-family-monospace">\\192.168.1.6</span>
  </p>
  <figure class="image max-800 is-bordered">
    <img src={surl('/assets/guides/virtualbox/samba.png')} alt="Samba sharing" loading="lazy" />
  </figure>
</div>

<BackToTop />
