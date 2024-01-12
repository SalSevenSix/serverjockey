<script>
  import { getContext } from 'svelte';
  import { notifyError } from '$lib/util/notifications';
  import { newPostRequest } from '$lib/util/sjgmsapi';

  const instance = getContext('instance');
  const serverStatus = getContext('serverStatus');
  const eventDown = getContext('eventDown');
  const autoOptions = ['Off', 'Start', 'Restart', 'Start and Restart'];

  let currentOption = null;
  let selectedOption = null;

  $: cannotChange = $serverStatus.running || $serverStatus.state === 'MAINTENANCE';

  $: if ($eventDown) {
    currentOption = autoOptions[$serverStatus.auto];
    selectedOption = currentOption;
  }

  $: if ($serverStatus.auto > -1) {
    if (selectedOption === null) {
      currentOption = autoOptions[$serverStatus.auto];
      selectedOption = currentOption;
    }
  }

  $: if (selectedOption) {
    if (currentOption != selectedOption) {
      let originalOption = currentOption;
      currentOption = selectedOption;  // lock it in now to block another trigger
      let request = newPostRequest();
      request.body = JSON.stringify({ auto: autoOptions.indexOf(selectedOption) });
      fetch(instance.url(), request)
        .then(function(response) {
          if (!response.ok) throw new Error('Status: ' + response.status);
        })
        .catch(function(error) {
          currentOption = originalOption;  // safe rollback
          selectedOption = originalOption;
          notifyError('Failed to update Auto mode.');
        });
    }
  }
</script>


<div class="block field is-horizontal">
  <div class="field-label is-normal">
    <label for="serverConfigAuto" class="label" title="Auto mode">Auto</label>
  </div>
  <div class="field-body">
    <div class="field is-narrow">
      <div class="control select">
        <select id="serverConfigAuto" disabled={cannotChange} bind:value={selectedOption}>
          {#each autoOptions as option}
            <option>{option}</option>
          {/each}
        </select>
      </div>
    </div>
  </div>
</div>
