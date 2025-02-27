<script>
  import { getContext } from 'svelte';
  import { slide } from 'svelte/transition';
  import { fNoop, fTrue } from '$lib/util/util';
  import { newPostRequest } from '$lib/util/sjgmsapi';
  import { notifyInfo, notifyError } from '$lib/util/notifications';
  import SpinnerIcon from '$lib/widget/SpinnerIcon.svelte';

  const instance = getContext('instance');
  const serverStatus = getContext('serverStatus');

  export let idPrefix;
  export let rootPath;
  export let filenameHelp = 'Please choose a valid filename.';
  export let validateFilename = fTrue;
  export let onCompleted = fNoop;
  export let multiple = false;

  let uploading = false;
  let selectedFiles = [];

  $: cannotUpload = selectedFiles.length === 0 || uploading || $serverStatus.state === 'MAINTENANCE';
  $: displayName = makeDisplayName(selectedFiles); function makeDisplayName(files) {
    if (files.length === 0) return 'No file selected';
    if (files.length === 1) return files[0].name;
    return files[0].name + ' (+' + (files.length - 1) + ' more)';
  }

  async function uploadFiles() {
    for (const file of selectedFiles) {
      const request = newPostRequest(null);
      request.body = new FormData();
      request.body.append('file', file);
      const successful = await fetch(instance.url(rootPath + '/' + file.name), request)
        .then(function(response) {
          if (!response.ok) throw new Error('Status: ' + response.status);
          return notifyInfo(file.name + ' uploaded successfully.', true);
        })
        .catch(function() {
          return notifyError('Failed to upload ' + file.name, false);
        });
      if (!successful) return;
    }
  }

  function actionUpload() {
    if (cannotUpload) return;
    for (const file of selectedFiles) {
      if (!validateFilename(file.name)) return notifyError(filenameHelp);
    }
    uploading = true;
    uploadFiles().finally(function() {
      uploading = false;
      onCompleted();
    });
  }
</script>


{#if uploading}
  <div transition:slide={{ delay: 250, duration: 500 }}>
    <p id="{idPrefix}Uploading" class="mb-3 has-text-weight-bold">
      <SpinnerIcon /> Please keep this section open while uploading. See console log for upload progress.
    </p>
  </div>
{/if}

<div class="file is-fullwidth is-info has-name">
  <div class="control buttons mb-0 mr-2">
    <button id="{idPrefix}ActionUpload" title="Upload File" class="button is-success"
            disabled={cannotUpload} on:click={actionUpload}>
      <i class="fa fa-file-arrow-up fa-lg"></i>&nbsp;&nbsp;Upload</button>
  </div>
  <label class="file-label pr-6">
    <input id="{idPrefix}Filename" class="file-input" type="file" {multiple} bind:files={selectedFiles}>
    <span class="file-cta" title={filenameHelp}>
      <span class="file-icon"><i class="fa fa-file-circle-plus"></i></span>
      <span class="file-label">Choose file…</span>
    </span>
    <span class="file-name" title={filenameHelp}>{displayName}</span>
  </label>
</div>
