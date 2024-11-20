<script>
  import { onMount } from 'svelte';
  import { surl, newGetRequest, newPostRequest } from '$lib/util/sjgmsapi';
  import { notifyInfo, notifyError } from '$lib/util/notifications';
  import { confirmModal } from '$lib/modal/modals';

  let httpsInfo = null;
  let processing = false;

  $: httpsAction = httpsInfo && httpsInfo.enabled ? 'Disable' : 'Enable';
  $: httpsClass = httpsInfo && httpsInfo.enabled ? 'is-danger' : 'is-primary';
  $: httpsIcon = httpsInfo && httpsInfo.enabled ? 'fa-square-xmark' : 'fa-shield';

  function toggleHttps() {
    const change = httpsInfo.enabled ? 'disable' : 'enable';
    confirmModal('Are you sure you want to ' + change + ' HTTPS ?', function() {
      processing = true;
      const request = newPostRequest();
      request.body = JSON.stringify({ enabled: !httpsInfo.enabled });
      fetch(surl('/ssl'), request)
        .then(function(response) {
          if (!response.ok) throw new Error('Status: ' + response.status);
          httpsInfo.enabled = !httpsInfo.enabled;
          notifyInfo('Successfully ' + change + 'd HTTPS.');
        })
        .catch(function(error) { notifyError('Failed to ' + change + ' HTTPS.'); })
        .finally(function() { processing = false; });
    });
  }

  onMount(function() {
    fetch(surl('/ssl'), newGetRequest())
      .then(function(response) {
        if (!response.ok) throw new Error('Status: ' + response.status);
        return response.json();
      })
      .then(function(json) { httpsInfo = json; })
      .catch(function(error) { notifyError('Failed to load HTTPS info.'); });
  });
</script>


{#if httpsInfo}
  <div class="columns">
    <div class="column is-one-quarter">
      <button id="httpsControlsToggle" class="button {httpsClass}" title={httpsAction}
              disabled={processing} on:click={toggleHttps}>
        <i class="fa {httpsIcon} fa-lg"></i>&nbsp; {httpsAction} HTTPS</button>
    </div>
    <div class="column is-three-quarters">
      Change takes effect after system restart. Note that when enabled, a self-signed certificate will be used.
      Browsers will issue security warnings because certificate ownership is not verified by a 3rd party.
      However all data sent between browser and server will be encrypted and private.
    </div>
  </div>
{/if}
