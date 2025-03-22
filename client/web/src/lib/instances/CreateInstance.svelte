<script>
  import { onMount } from 'svelte';
  import { notifyError } from '$lib/util/notifications';
  import { surl, newGetRequest, newPostRequest } from '$lib/util/sjgmsapi';
  import InputText from '$lib/widget/InputText.svelte';

  let modules = [];
  let serverForm = {};
  let processing = true;

  $: cannotEdit = processing || modules.length === 0;
  $: cannotCreate = cannotEdit || !serverForm.module || !serverForm.identity;

  function kpCreate(event) {
    if (event.key === 'Enter') { create(); }
  }

  function create() {
    if (cannotCreate) return;
    processing = true;
    const request = newPostRequest();
    request.body = JSON.stringify(serverForm);
    fetch(surl('/instances'), request)
      .then(function(response) {
        if (!response.ok) throw new Error('Status: ' + response.status);
        serverForm.identity = null;
      })
      .catch(function() { notifyError('Failed to create new instance.'); })
      .finally(function() { processing = false; });
  }

  onMount(function() {
    fetch(surl('/modules'), newGetRequest())
      .then(function(response) {
        if (!response.ok) throw new Error('Status: ' + response.status);
        return response.json();
      })
      .then(function(json) { modules = json; })
      .catch(function() { notifyError('Failed to load module list.'); })
      .finally(function() { processing = false; });
  });
</script>


<div class="content">
  <h2 class="title is-5">New Instance</h2>
  <div class="field">
    <label for="createInstanceModule" class="label" title="Module (game server)">Module</label>
    <p class="control has-icons-left">
      <span class="select is-fullwidth">
        <select id="createInstanceModule" disabled={cannotEdit} bind:value={serverForm.module}>
          {#each modules as module}
            <option class="notranslate">{module}</option>
          {/each}
        </select>
      </span>
      <span class="icon is-small is-left"><i class="fa fa-cube"></i></span>
    </p>
  </div>
  <InputText id="createInstanceIdentity" label="Name"
             bind:value={serverForm.identity} onKeypress={kpCreate} disabled={cannotEdit}
             title="Name for new Instance. Must be lower case letters and numbers, no spaces or special characters except dashes and underscores." />
  <div class="block buttons mt-4">
    <button id="createInstanceCreate" title="Create" class="button is-primary is-fullwidth"
            disabled={cannotCreate} on:click={create}>
      <i class="fa-solid fa-square-plus fa-lg"></i>&nbsp;&nbsp;Create</button>
  </div>
</div>
