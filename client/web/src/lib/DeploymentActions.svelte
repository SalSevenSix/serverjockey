<script>
  import { capitalizeKebabCase } from '$lib/util';
  import { instance, serverStatus, newPostRequest } from '$lib/serverjockeyapi';

  export let actions = {};

	function doAction() {
    if (!confirm('Are you sure you want to ' + capitalizeKebabCase(this.name) + ' ?')) return;
    fetch($instance.url + '/deployment/' + this.name, newPostRequest())
      .then(function(response) { if (!response.ok) throw new Error('Status: ' + response.status); })
      .catch(function(error) { alert('Error ' + error); });
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
