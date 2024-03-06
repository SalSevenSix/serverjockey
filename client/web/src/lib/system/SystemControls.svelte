<script>
  import { onMount } from 'svelte';
  import { newGetRequest, newPostRequest } from '$lib/util/sjgmsapi';
  import { notifyInfo, notifyError } from '$lib/util/notifications';
  import { confirmModal } from '$lib/modal/modals';
  import Collapsible from '$lib/widget/Collapsible.svelte';

  let httpsInfo = null;
  let processing = false;

  $: httpsLabel = httpsInfo && httpsInfo.enabled ? 'Disable HTTPS' : 'Enable HTTPS';
  $: httpsClass = httpsInfo && httpsInfo.enabled ? 'is-danger' : 'is-primary';
  $: httpsIcon = httpsInfo && httpsInfo.enabled ? 'fa-square-xmark' : 'fa-shield';

  function toggleHttps() {
    const change = httpsInfo.enabled ? 'disable' : 'enable';
    confirmModal('Are you sure you want to ' + change + ' HTTPS ?', function() {
      processing = true;
      const request = newPostRequest();
      request.body = JSON.stringify({ enabled: !httpsInfo.enabled });
      fetch('/ssl', request)
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
    fetch('/ssl', newGetRequest())
      .then(function(response) {
        if (!response.ok) throw new Error('Status: ' + response.status);
        return response.json();
      })
      .then(function(json) { httpsInfo = json; })
      .catch(function(error) { notifyError('Failed to load HTTPS info.'); });
  });
</script>


<Collapsible icon="fa-gears" title="System">
  <div class="columns">
    <div class="column is-one-quarter">
      <a href="/system/log" title="Open" target="_blank">
        &nbsp; View Log &nbsp;<i class="fa fa-up-right-from-square fa-lg"></i></a>
    </div>
    <div class="column is-three-quarters">
      Open system log in a new tab.
    </div>
  </div>
  {#if httpsInfo}
    <div class="columns">
      <div class="column is-one-quarter">
        <button class="button {httpsClass}" disabled={processing} on:click={toggleHttps}>
          <i class="fa {httpsIcon} fa-lg"></i>&nbsp; {httpsLabel}</button>
      </div>
      <div class="column is-three-quarters">
        Change takes effect after system restart. Note that when enabled, a self-signed certificate will be used.
        Browsers will issue security warnings because certificate ownership is not verified by a 3rd party.
        However all data sent between browser and server will be encrypted and private.
      </div>
    </div>
  {/if}
</Collapsible>
