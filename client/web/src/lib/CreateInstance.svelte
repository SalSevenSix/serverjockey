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

  function kpCreate(event) {
    if (event.key === 'Enter') { create(); }
  }

  function create() {
    if (!serverForm.module) return notifyError('Module not selected.');
    if (!serverForm.identity) return notifyError('Name not set.');
    creating = true;
    let request = newPostRequest();
    request.body = JSON.stringify(serverForm);
    fetch(baseurl + '/instances', request)
      .then(function(response) {
        if (!response.ok) throw new Error('Status: ' + response.status);
        serverForm.identity = null;
      })
      .catch(function(error) { notifyError('Failed to create new instance.'); })
      .finally(function() { creating = false; });
  }
</script>


<div class="block">
  <h2 class="title is-5">New Instance</h2>
  <div class="field">
    <label for="createInstanceModule" class="label" title="Module (game server)">Module</label>
    <div class="control">
      <div class="select">
        <select id="createInstanceModule" disabled={creating} bind:value={serverForm.module}>
          {#each modules as module}
            <option>{module}</option>
          {/each}
        </select>
      </div>
    </div>
  </div>
  <div class="field">
    <label for="createInstanceIdentity" class="label"
           title="Name for new Instance. Must be lower case letters and numbers, no spaces or special characters except dashes and underscores">
      Name</label>
    <div class="control">
      <input id="createInstanceIdentity" class="input" type="text"
             disabled={creating} on:keypress={kpCreate} bind:value={serverForm.identity}>
    </div>
  </div>
  <div class="block buttons">
    <button name="create" title="Create" class="button is-primary is-fullwidth" disabled={creating} on:click={create}>
      <i class="fa-solid fa-folder-plus fa-lg"></i>&nbsp;&nbsp;Create</button>
  </div>
</div>
