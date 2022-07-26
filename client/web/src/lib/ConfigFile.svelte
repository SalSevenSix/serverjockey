<script>
  import { onMount } from 'svelte';
	import { instance, newPostRequest, newGetRequest, openFileInNewTab } from '$lib/serverjockeyapi';

  export let name;
  export let path;
  let updating = false;
  let configText = '';

	onMount(async function() {
	  reload();
	});

	function openConfigFile() {
	  openFileInNewTab($instance.url + path);
	}

	function clear() {
	  configText = '';
	}

	function reload() {
	  updating = true;
	  fetch($instance.url + path, newGetRequest())
      .then(function(response) {
        if (!response.ok) throw new Error('Status: ' + response.status);
        return response.text();
      })
      .then(function(text) { configText = text; })
      .catch(function(error) { clear(); })
      .finally(function() { updating = false; });
	}

	function update() {
	  updating = true;
    let request = newPostRequest('text/plain');
    request.body = configText;
    fetch($instance.url + path, request)
      .then(function(response) { if (!response.ok) throw new Error('Status: ' + response.status); })
      .catch(function(error) { alert('Error ' + error); })
      .finally(function() { updating = false; });
	}
</script>


<div class="block">
  <div class="field">
    <label class="label"><a href="#" on:click|preventDefault={openConfigFile}>{name}</a></label>
    <div class="control pr-6">
      <textarea class="textarea" bind:value={configText}></textarea>
    </div>
  </div>
  <div class="field">
    <div class="control buttons">
      <button disabled={updating} name="clear" class="button is-danger" on:click={clear}>Clear</button>
      <button disabled={updating} name="reload" class="button is-warning" on:click={reload}>Reload</button>
      <button disabled={updating} name="update" class="button is-primary" on:click={update}>Update</button>
    </div>
  </div>
</div>
