<script>
  import { dev } from '$app/env';
  import { notifyError } from '$lib/notifications';
  import { baseurl, newPostRequest } from '$lib/serverjockeyapi';

  let serverForm = {};
  let creating = false;

	function create() {
	  if (!serverForm.identity) return notifyError('Instance Name not set.');
	  creating = true;
	  serverForm.identity = serverForm.identity.replaceAll(' ', '-').toLowerCase();
    let request = newPostRequest();
    request.body = JSON.stringify(serverForm);
    fetch(baseurl + '/instances', request)
      .then(function(response) {
        if (!response.ok) throw new Error('Status: ' + response.status);
        serverForm.identity = null;
      })
      .catch(function(error) { notifyError('Failed to create new server.'); })
      .finally(function() { creating = false; });
	}
</script>


<div class="block">
  <h2 class="title is-5">New Instance</h2>
  <div class="field">
    <label for="createinstance-module" class="label">Instance Type</label>
    <div class="control">
      <div class="select">
        <select id="createinstance-module" bind:value={serverForm.module}>
          {#if dev}<option>testserver</option>{/if}
          <option>projectzomboid</option>
          <option>factorio</option>
        </select>
      </div>
    </div>
  </div>
  <div class="field">
    <label for="createinstance-instance" class="label">Instance Name</label>
    <div class="control">
      <input id="createinstance-instance" class="input" type="text" bind:value={serverForm.identity}>
    </div>
  </div>
  <div class="field">
    <div class="control">
      <button id="createinstance-create" disabled={creating} name="create" class="button is-primary is-fullwidth" on:click={create}>Create</button>
    </div>
  </div>
</div>
