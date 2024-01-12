<script>
  import { onMount, getContext } from 'svelte';
  import { confirmModal } from '$lib/modal/modals';
  import { shortISODateTimeString } from '$lib/util/util';
  import { newGetRequest, newPostRequest } from '$lib/util/sjgmsapi';
  import { notifyInfo, notifyError } from '$lib/util/notifications';
  import SpinnerIcon from '$lib/widget/SpinnerIcon.svelte';

  const instance = getContext('instance');
  const serverStatus = getContext('serverStatus');
  const eventDown = getContext('eventDown');
  const eventStarted = getContext('eventStarted');
  const eventEndMaint = getContext('eventEndMaint');

  export let actions = [];

  let processing = true;
  let lastActivity = null;

  $: cannotAction = processing || $serverStatus.running || $serverStatus.state === 'MAINTENANCE';
  $: if ($eventDown || $eventStarted || $eventEndMaint) { loadWorldMeta(); }

  function doAction() {
    let actionKey = this.name;
    let actionTitle = this.title;
    confirmModal('Are you sure you want to ' + actionTitle + ' ?\nThis action cannot be undone.', function() {
      processing = true;
      fetch(instance.url('/deployment/' + actionKey), newPostRequest())
        .then(function(response) {
          if (!response.ok) throw new Error('Status: ' + response.status);
          notifyInfo(actionTitle + ' completed.');
        })
        .catch(function(error) { notifyError(actionTitle + ' failed.'); })
        .finally(loadWorldMeta);
    });
  }

  function loadWorldMeta() {
    processing = true;
    fetch(instance.url('/deployment/world-meta'), newGetRequest())
      .then(function(response) {
        if (!response.ok) throw new Error('Status: ' + response.status);
        return response.json();
      })
      .then(function(json) { lastActivity = json.timestamp ? shortISODateTimeString(json.timestamp) : 'None'; })
      .catch(function(error) { notifyError('Failed to load World meta.'); })
      .finally(function() { processing = false; });
  }

  onMount(loadWorldMeta);
</script>


<div class="content">
  <h3 class="title is-5 mb-3">World</h3>
  <p><span class="has-text-weight-bold">Last Activity:</span>&nbsp;
    {#if processing && !lastActivity}
      <SpinnerIcon /> loading...
    {:else if lastActivity === 'None'}
      <span class="is-italic">not found, world may not exist</span>
    {:else if lastActivity}
      {lastActivity}
    {:else}
      <span class="is-italic">unavailable</span>
    {/if}
  </p>
  <table class="table"><tbody>
    {#each actions as action}
      <tr>
        <td class="button-column">
          <button title={action.name} class="button is-danger is-fullwidth"
                  name={action.key} disabled={cannotAction} on:click={doAction}>
            <i class="fa {action.icon ? action.icon : 'fa-burst'} fa-lg"></i>&nbsp; {action.name}</button>
        </td>
        <td>{action.desc}</td>
      </tr>
    {/each}
  </tbody></table>
</div>


<style>
  .button-column {
    width: 20%;
  }
</style>
