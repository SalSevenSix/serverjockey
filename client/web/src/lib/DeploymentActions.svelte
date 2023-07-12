<script>
  import { capitalizeKebabCase } from '$lib/util';
  import { confirmModal } from '$lib/modals';
  import { notifyInfo, notifyError } from '$lib/notifications';
  import { newPostRequest } from '$lib/sjgmsapi';
  import { instance, serverStatus } from '$lib/instancestores';

  export let actions = [];

  let processing = false;

  $: cannotAction = processing || $serverStatus.running || $serverStatus.state === 'MAINTENANCE';

  function doAction() {
    let actionKey = this.name;
    let actionTitle = this.title;
    confirmModal('Are you sure you want to ' + actionTitle + ' ?', function() {
      processing = true;
      fetch($instance.url + '/deployment/' + actionKey, newPostRequest())
        .then(function(response) {
          if (!response.ok) throw new Error('Status: ' + response.status);
          notifyInfo(actionTitle + ' completed.');
        })
        .catch(function(error) { notifyError(actionTitle + ' failed.'); })
        .finally(function() { processing = false; });
    });
  }
</script>


<div class="block">
  <table class="table">
    <tbody>
      {#each actions as action}
        <tr>
          <td>
            <button name={action.key} title={capitalizeKebabCase(action.key)} class="button is-danger is-fullwidth"
                    disabled={cannotAction} on:click={doAction}>
              <i class="fa {action.icon ? action.icon : 'fa-burst'} fa-lg"></i>&nbsp;&nbsp;{action.name}</button>
          </td>
          <td>{action.desc}</td>
        </tr>
      {/each}
    </tbody>
  </table>
</div>
