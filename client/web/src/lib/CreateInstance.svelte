<script>
  import { onMount } from 'svelte';
  import { notifyError } from '$lib/notifications';
  import { baseurl, newGetRequest, newPostRequest } from '$lib/serverjockeyapi';

  let modules = [];
  let serverForm = {};
  let creating = false;

	onMount(function() {
    fetch(baseurl + '/modules', newGetRequest())
      .then(function(response) {
        if (!response.ok) throw new Error('Status: ' + response.status);
        return response.json();
      })
      .then(function(json) {
        modules = json;
      })
      .catch(function(error) { notifyError('Failed to load module list.'); });
  });

	function create() {
	  if (!serverForm.module) return notifyError('Type not selected.');
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
    <label for="createinstance-module" class="label">Type</label>
    <div class="control">
      <div class="select">
        <select id="createinstance-module" bind:value={serverForm.module}>
          {#each modules as module}
            <option>{module}</option>
          {/each}
        </select>
      </div>
    </div>
  </div>
  <div class="field">
    <label for="createinstance-instance" class="label">Name</label>
    <div class="control">
      <input id="createinstance-instance" class="input" type="text" bind:value={serverForm.identity}>
    </div>
  </div>
  <div class="field">
    <div class="control">
      <button id="createinstance-create" name="create" class="button is-primary is-fullwidth"
              disabled={creating} on:click={create}>Create</button>
    </div>
  </div>
</div>
