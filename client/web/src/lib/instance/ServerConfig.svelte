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

  $: cannotChange = $serverStatus.running != false || $serverStatus.state === 'MAINTENANCE';

  $: if ($eventDown) {
    currentOption = autoOptions[$serverStatus.auto];
    selectedOption = currentOption;
  }

  $: serverStatusUpdated($serverStatus.auto); function serverStatusUpdated(auto) {
    if (selectedOption === null && auto > -1) {
      currentOption = autoOptions[$serverStatus.auto];
      selectedOption = currentOption;
    }
  }

  $: selectedOptionUpdated(selectedOption); function selectedOptionUpdated() {
    if (!selectedOption || currentOption === selectedOption) return;
    const originalOption = currentOption;
    currentOption = selectedOption;  // Lock it in now to block another trigger
    const request = newPostRequest();
    request.body = JSON.stringify({ auto: autoOptions.indexOf(selectedOption) });
    fetch(instance.url(), request)
      .then(function(response) {
        if (!response.ok) throw new Error('Status: ' + response.status);
      })
      .catch(function() {
        currentOption = originalOption;  // Safe rollback
        selectedOption = originalOption;
        notifyError('Failed to update Auto mode.');
      });
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
