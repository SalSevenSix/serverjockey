<script>
  import { capitalizeKebabCase } from '$lib/util';
  import { confirmModal } from '$lib/modals';
  import { notifyInfo, notifyError } from '$lib/notifications';
  import { instance, serverStatus, newPostRequest } from '$lib/serverjockeyapi';

  export let actions = {};

	function doAction() {
	  let actionName = this.name;
	  let actionDisplay = capitalizeKebabCase(actionName);
    confirmModal('Are you sure you want to ' + actionDisplay + ' ?', function() {
      fetch($instance.url + '/deployment/' + actionName, newPostRequest())
        .then(function(response) {
          if (!response.ok) throw new Error('Status: ' + response.status);
          notifyInfo(actionDisplay + ' completed.');
        })
        .catch(function(error) { notifyError(actionDisplay + ' failed.'); });
    });
	}
</script>


<div class="block">
  <table class="table">
    <tbody>
      {#each Object.keys(actions) as name}
        <tr>
          <td><button id="{name}-button" disabled={$serverStatus.running} name="{name}" class="button is-primary is-fullwidth" on:click={doAction}>{capitalizeKebabCase(name)}</button></td>
          <td>{actions[name]}</td>
        </tr>
      {/each}
    </tbody>
  </table>
</div>
