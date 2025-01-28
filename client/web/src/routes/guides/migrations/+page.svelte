<script>
  import { surl } from '$lib/util/sjgmsapi';
  import ExtLink from '$lib/widget/ExtLink.svelte';
  import BackToTop from '$lib/widget/BackToTop.svelte';
</script>


<div class="columns">
  <div class="column is-one-quarter content mb-0">
    <p class="has-text-centered pt-2">
      <i class="fa fa-dolly fa-8x theme-black-white"></i>
    </p>
  </div>
  <div class="column is-three-quarters content">
    <h2 class="title is-3 mt-2">Game Save Migrations</h2>
    <p>
      An existing game save (world) can be migrated into ServerJockey using the Backup &amp; Restore feature.
      This guide will show how this is done using Project Zomboid as an example. The process can be used
      for to all supported games, both for migration and simply to copy game saves between instances.
    </p>
  </div>
</div>

<div class="content">
  <p><span class="step-title"></span>
    First step for migration is to follow the appropriate
    <a href={surl('/guides#gameserverguides')}>game server guide</a>
    to create a new instance with game server installed and started once.
    This will ensure a new game save is created as a fresh example.
  </p>
  <figure class="image max-1024 is-bordered">
    <img src={surl('/assets/guides/migrations/fresh_world.png')} alt="Create fresh game save world" />
  </figure>
</div>

<div class="content">
  <p><span class="step-title"></span>
    After the server has been stopped, find and expand the
    <span class="has-text-weight-bold">Backups</span>
    section. Click the
    <span class="has-text-weight-bold">Backup World</span>
    button to create a zip file backup of the game save.
    Then download the zip backup to your local machine and unpack into an empty folder.
    For the guide I am using the free
    <ExtLink href="https://www.7-zip.org" notranslate>7-zip</ExtLink>
    app.
  </p>
  <figure class="image max-1024 is-bordered">
    <img src={surl('/assets/guides/migrations/backup_world.png')} alt="Create world backup zip" loading="lazy" />
  </figure>
</div>

<div class="content">
  <p><span class="step-title"></span>
    Note the top level files &amp; folders in the zip backup. They will be different depending upon the game,
    but they should match the existing game save you want to migrate. Now find the location of the save game
    you want to migrate. Then delete the files &amp; folders downloaded, and copy-paste to replace them with
    the files &amp; folders from your game save.
  </p>
  <figure class="image max-600 is-bordered">
    <img src={surl('/assets/guides/migrations/unpack_world.png')} alt="Unpacked world backup zip" loading="lazy" />
  </figure>
</div>

<div class="content">
  <p><span class="step-title"></span>
    Group select all the the files &amp; folders and pack them into a zip file with a name starting with
    &nbsp;<span class="is-family-monospace has-text-weight-bold notranslate">world-</span>&nbsp;
    for the guide I called it
    &nbsp;<span class="is-family-monospace white-space-nowrap notranslate">world-migrated.zip</span>
  </p>
  <p>
    Compare the zip file downloaded to the new zip file containing the game save to migrate.
    Ensure that the top level files &amp; folders are the same.
  </p>
  <figure class="image max-800 is-bordered">
    <img src={surl('/assets/guides/migrations/verify_migrated.png')} alt="Verify migration zip" loading="lazy" />
  </figure>
</div>

<div class="content">
  <p><span class="step-title"></span>
    Now upload the migration game save zip, then restore it.
    After this has been done, the existing save should be successfully migrated into the instance!
  </p>
  <figure class="image max-1024 is-bordered">
    <img src={surl('/assets/guides/migrations/restore_world.png')} alt="Upload and restore migration" loading="lazy" />
  </figure>
  <p>
    <span class="has-text-weight-bold">Note</span>
    that this overall process can be used to simply copy game saves between ServerJockey instances.
    However you only need to create a world backup, download it, then upload it to the target instance and restore it.
  </p>
</div>

<BackToTop />
