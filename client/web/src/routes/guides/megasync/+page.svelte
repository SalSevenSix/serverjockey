<script>
  import { surl } from '$lib/util/sjgmsapi';
  import MegaUploadIcon from '$lib/svg/MegaUploadIcon.svelte';
  import BackToTop from '$lib/widget/BackToTop.svelte';
  import ExtLink from '$lib/widget/ExtLink.svelte';
  import CodeBlock from '$lib/widget/CodeBlock.svelte';
  import NanoGuide from '$lib/widget/NanoGuide.svelte';
</script>


<div class="columns">
  <div class="column is-one-quarter content mb-0 pb-0">
    <figure class="image mt-2 max-200"><MegaUploadIcon /></figure>
  </div>
  <div class="column is-three-quarters content">
    <h2 class="title is-3 mt-2">Offsite backups using MEGA</h2>
    <p>
      <ExtLink href="https://mega.io" notranslate>MEGA</ExtLink>
      is a free cloud storage service you can use for off-site backups.
      This guide will show you how to install and configure the MEGA CMD App on your machine,
      then setup the Sync feature to automatically copy backups.
      Prequisites are a user with root privilages (i.e.
      <span class="is-family-monospace notranslate">sudo</span>)
      and terminal access to the machine with familiarity using it.
    </p>
  </div>
</div>

<div class="content">
  <p><span class="step-title"></span>
    If you are new to MEGA, then the first step is to
    <ExtLink href="https://mega.nz/register">register a new account</ExtLink>
    on free-tier to begin.
  </p>
  <figure class="image max-1024">
    <img src={surl('/assets/guides/megasync/mega_dashboard.png')} alt="Dashboard of new MEGA account" />
  </figure>

  <p><span class="step-title"></span>
    Folders must be created first on MEGA to hold the backup files. Navigate to the
    <span class="has-text-weight-bold">Cloud drive</span>
    then use the
    <span class="has-text-weight-bold">Create folder</span>
    button to build a folder structure. For the guide, I created a
    <span class="is-family-monospace notranslate">serverjockey</span>
    folder then a
    <span class="is-family-monospace notranslate">myserver</span>
    folder to hold backup files for the instance of the same name.
  </p>
  <figure class="image max-1024">
    <img src={surl('/assets/guides/megasync/create_folders.png')} alt="Create folders on MEGA" loading="lazy" />
  </figure>

  <p><span class="step-title"></span>
    Now install the
    <ExtLink href="https://mega.io/cmd#download" notranslate>MEGA CMD App</ExtLink>
    by visiting the website to find and run the appropriate install command for your system.
    As an example for the guide, the command below is for Ubuntu 24.04 on an Intel or AMD machine.
  </p>
  <CodeBlock>wget https://mega.nz/linux/repo/xUbuntu_24.04/amd64/megacmd-xUbuntu_24.04_amd64.deb && sudo apt install &quot;$PWD/megacmd-xUbuntu_24.04_amd64.deb&quot;</CodeBlock>
  <figure class="image max-1024">
    <img src={surl('/assets/guides/megasync/install_megacmd.png')} alt="Install MEGA CMD in terminal" loading="lazy" />
  </figure>

  <p><span class="step-title"></span>
    Now login to MEGA using the MEGA CMD App, so that credentials will not be
    solicited again when app tools are used later. Use the command show below
    <span class="is-italic">but with your</span>
    <span class="has-text-weight-bold notranslate">email</span>
    <span class="is-italic">and</span>
    <span class="has-text-weight-bold notranslate">password</span>.
  </p>
  <p>
    Note that this command is run as the default ServerJockey user
    (<span class="is-family-monospace notranslate">sjgms</span>)
    so that app configuration is stored with that user. Also,
    if you do not want to enter a clear text password, see the other login options using
    &nbsp;<span class="is-family-monospace white-space-nowrap notranslate">mega-login --help</span>
  </p>
  <CodeBlock>sudo su - sjgms -s /bin/bash -c &quot;mega-login email password&quot;</CodeBlock>
  <p>
    Any MEGA CMD command including login will start the MEGA CMD background server process.
    Stop this process using the command shown below, because it will be setup as a systemd service in the next steps.
  </p>
  <CodeBlock>sudo kill $(pidof mega-cmd-server)</CodeBlock>

  <p><span class="step-title"></span>
    Now setup MEGA CMD server as a systemd service for the default ServerJockey user
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
    With login credentials saved and the MEGA CMD service running,
    the synchronisation/mirroring of backup files with MEGA can be configured.
    The example command below will add persistent synchronisation between
    the local folder containing backups for instance
    <span class="has-text-weight-bold notranslate">myserver</span>
    and the remote folder created for it on MEGA.
  </p>
  <CodeBlock>sudo su - sjgms -s /bin/bash -c &quot;mega-sync /home/sjgms/myserver/backups /serverjockey/myserver&quot;</CodeBlock>
  <p><span class="has-text-weight-bold">Hint:</span>
    You can view all synchronisation entries simply by running the sync command as shown below.
  </p>
  <CodeBlock>sudo su - sjgms -s /bin/bash -c &quot;mega-sync&quot;</CodeBlock>

  <p><span class="step-title"></span>
    With offsite backups setup using MEGA CMD synchronisation, it can be tested simply by creating
    a backup in ServerJockey. Any backup zip file created for the instance should be automatically
    copied to MEGA in the designated folder.
  </p>
  <figure class="image max-800 is-bordered">
    <img src={surl('/assets/guides/megasync/create_backup.png')} alt="Create myserver world backup" loading="lazy" />
  </figure>
  <figure class="image max-800 is-bordered">
    <img src={surl('/assets/guides/megasync/backup_synced.png')} alt="Backup synced on MEGA" loading="lazy" />
  </figure>

  <p class="is-size-5 has-text-weight-bold">Addendum</p>
  <p>MEGA synchronisation is bi-directional. The synchronisation behaviour when files or folders are deleted;</p>
  <ul>
    <li>
      If you move a backup file to rubbish bin in MEGA. In ServerJockey, the file will be moved into a folder called
      <span class="has-text-weight-bold notranslate">.debris</span>
      in the instance backups. Deleting debris will not effect MEGA.
    </li>
    <li>
      If you delete a backup file in ServerJockey. In MEGA,
      the file will be moved into rubbish bin under a folder called
      <span class="has-text-weight-bold notranslate">SyncDebris</span>.
    </li>
    <li>
      If you delete an instance in ServerJockey. In MEGA, the files will usually be moved into rubbish bin,
      but they may remain in the designated folder. Also, the synchronisation entry will be disabled but not removed.
    </li>
  </ul>

</div>

<BackToTop />
