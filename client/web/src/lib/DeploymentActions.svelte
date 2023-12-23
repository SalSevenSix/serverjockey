<script>
  import { getContext } from 'svelte';
  import { confirmModal } from '$lib/modals';
  import { notifyInfo, notifyError } from '$lib/notifications';
  import { newPostRequest } from '$lib/sjgmsapi';

  const instance = getContext('instance');
  const serverStatus = getContext('serverStatus');

  export let actions = [];

  let processing = false;

  $: cannotAction = processing || $serverStatus.running || $serverStatus.state === 'MAINTENANCE';

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
        .finally(function() { processing = false; });
    });
  }
</script>


<div class="content">
  <h3 class="title is-5 mb-3">World</h3>
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
