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

  let uploading = false;
  let uploadFiles = [];

  $: noFileSelected = uploadFiles.length === 0;
  $: cannotUpload = uploading || $serverStatus.state === 'MAINTENANCE';

  function uploadFile() {
    if (noFileSelected) return;
    const filename = uploadFiles[0].name;
    if (!validateFilename(filename)) return notifyError(filenameHelp);
    uploading = true;
    const request = newPostRequest(null);
    request.body = new FormData();
    request.body.append('file', uploadFiles[0]);
    fetch(instance.url(rootPath + '/' + filename), request)  // Blocks until complete
      .then(function(response) {
        if (!response.ok) throw new Error('Status: ' + response.status);
        notifyInfo(filename + ' uploaded successfully.');
      })
      .catch(function() {
        notifyError('Failed to upload ' + filename);
      })
      .finally(function() {
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
    <button id="{idPrefix}UploadFile" title="Upload File" class="button is-success"
            disabled={noFileSelected || cannotUpload} on:click={uploadFile}>
      <i class="fa fa-file-arrow-up fa-lg"></i>&nbsp;&nbsp;Upload</button>
  </div>
  <label class="file-label pr-6">
    <input id="{idPrefix}Filename" class="file-input" type="file" bind:files={uploadFiles}>
    <span class="file-cta" title={filenameHelp}>
      <span class="file-icon"><i class="fa fa-file-circle-plus"></i></span>
      <span class="file-label">Choose file…</span>
    </span>
    <span class="file-name" title={filenameHelp}>
      {noFileSelected ? 'No file selected' : uploadFiles[0].name}
    </span>
  </label>
</div>
