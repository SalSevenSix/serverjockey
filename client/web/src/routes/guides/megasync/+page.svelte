<script>
  import { surl } from '$lib/util/sjgmsapi';
  import BackToTop from '$lib/widget/BackToTop.svelte';
  import ExtLink from '$lib/widget/ExtLink.svelte';
  import CodeBlock from '$lib/widget/CodeBlock.svelte';
  import NanoGuide from '$lib/widget/NanoGuide.svelte';
</script>


<div class="columns">
  <div class="column is-one-quarter content mb-0">
    <p class="has-text-centered pt-2">
      <i class="fa fa-boxes-packing fa-7x theme-black-white"></i>
    </p>
  </div>
  <div class="column is-three-quarters content">
    <h2 class="title is-3 mt-2">Offsite backups using MEGA</h2>
    <p>
      TODO
      <ExtLink href="https://mega.io" notranslate>MEGA</ExtLink>
    </p>
  </div>
</div>

<div class="content">
  <p><span class="step-title"></span>
   TODO Register
  </p>
  <figure class="image max-1024">
    <img src={surl('/assets/guides/megasync/mega_dashboard.png')} alt="Dashboard of new MEGA account" />
  </figure>

  <p><span class="step-title"></span>
   TODO Create Folders
  </p>
  <figure class="image max-1024">
    <img src={surl('/assets/guides/megasync/create_folders.png')} alt="Create folders on MEGA" loading="lazy" />
  </figure>

  <p><span class="step-title"></span>
   TODO Install MEGA CMD
   <ExtLink href="https://mega.io/cmd#download" notranslate>MEGA CLI</ExtLink>
  </p>
  <CodeBlock>wget https://mega.nz/linux/repo/xUbuntu_24.04/amd64/megacmd-xUbuntu_24.04_amd64.deb && sudo apt install &quot;$PWD/megacmd-xUbuntu_24.04_amd64.deb&quot;</CodeBlock>
  <figure class="image max-1024">
    <img src={surl('/assets/guides/megasync/install_megacmd.png')} alt="Install MEGA CMD in terminal" loading="lazy" />
  </figure>

  <p><span class="step-title"></span>
   TODO Login MEGA CMD as sjgms
   <span class="has-text-weight-bold notranslate">email</span>
   and
   <span class="has-text-weight-bold notranslate">password</span>
   no likey see
   <span class="is-family-monospace notranslate">mega-login --help</span>
   for other options.
  </p>
  <CodeBlock>sudo su - sjgms -s /bin/bash -c &quot;mega-login email password&quot;</CodeBlock>
  <p>
   TODO Kill MEGA CMD
  </p>
  <CodeBlock>sudo kill $(pidof mega-cmd-server)</CodeBlock>

  <p><span class="step-title"></span>
    Now setup MEGA CMD as a systemd service for the default ServerJockey user
    <span class="is-family-monospace notranslate">sjgms</span>.
    <NanoGuide>to create the service file.</NanoGuide>
  </p>
  <CodeBlock>sudo nano /etc/systemd/system/mega-cmd-sjgms.service</CodeBlock>
  <p>
    Copy, paste and save the service configuration as shown below.
  </p>
  <CodeBlock>
[Unit]
Description=Mega CMD server for user sjgms
Requires=network.target
After=network.target

[Service]
Type=simple
Restart=on-failure
RestartSec=10
User=sjgms
ExecStart=/usr/bin/mega-cmd-server

[Install]
WantedBy=multi-user.target</CodeBlock>

  <p><span class="step-title"></span>
    With the service file created, signal systemd to load and apply all service files.
    Then enable and start the MEGA CMD service.
    When enabled, the service will automatically start when the machine starts.
  </p>
  <CodeBlock>sudo systemctl daemon-reload</CodeBlock>
  <CodeBlock>sudo systemctl enable mega-cmd-sjgms</CodeBlock>
  <CodeBlock>sudo systemctl start mega-cmd-sjgms</CodeBlock>
  <p><span class="has-text-weight-bold">Hint:</span>
    At any time you can check the status of the MEGA CMD service to see if it&#39;s running.
  </p>
  <CodeBlock>sudo systemctl status mega-cmd-sjgms</CodeBlock>
  <figure class="image max-1024">
    <img src={surl('/assets/guides/megasync/megacmd_status.png')} alt="MEGA CMD service status" loading="lazy" />
  </figure>

  <p><span class="step-title"></span>
   TODO Add myserver sync
  </p>
  <CodeBlock>sudo su - sjgms -s /bin/bash -c &quot;mega-sync /home/sjgms/myserver/backups /serverjockey/myserver&quot;</CodeBlock>
  <p><span class="has-text-weight-bold">Hint:</span>
   TODO
  </p>
  <CodeBlock>sudo su - sjgms -s /bin/bash -c &quot;mega-sync&quot;</CodeBlock>

  <p><span class="step-title"></span>
   TODO Test world backup
  </p>
  <figure class="image max-800">
    <img src={surl('/assets/guides/megasync/create_backup.png')} alt="Create myserver world backup" loading="lazy" />
  </figure>
  <figure class="image max-800">
    <img src={surl('/assets/guides/megasync/backup_synced.png')} alt="Backup synced on MEGA" loading="lazy" />
  </figure>

  <p><span class="has-text-weight-bold">Addendum.</span><br />
    TODO about what happens when folder/instance is deleted
  </p>

</div>

<BackToTop />
