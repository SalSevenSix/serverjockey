<script>
  import { dev } from '$app/env';
  import { baseurl, newPostRequest } from '$lib/serverjockeyapi';

  let serverForm = {};
  let creating = false;

	function create() {
	  creating = true;
    let request = newPostRequest();
    request.body = JSON.stringify(serverForm);
    fetch(baseurl + '/instances', request)
      .then(function(response) {
        creating = false;
        if (!response.ok) throw new Error('Status: ' + response.status);
        serverForm.identity = null;
      })
      .catch(function(error) { alert('Error ' + error); });
	}
</script>


<div class="block">
  <div class="field">
    <label for="module" class="label">Instance Type</label>
    <div class="control">
      <div class="select">
        <select id="module" bind:value={serverForm.module}>
          {#if dev}<option>testserver</option>{/if}
          <option>projectzomboid</option>
          <option>factorio</option>
        </select>
      </div>
    </div>
  </div>
  <div class="field">
    <label for="instance" class="label">Instance Name</label>
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
