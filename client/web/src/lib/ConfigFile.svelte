<script>
  import { onMount } from 'svelte';
  import { notifyInfo, notifyError } from '$lib/notifications';
  import { textAreaModal } from '$lib/modals';
  import { instance, newPostRequest, newGetRequest } from '$lib/serverjockeyapi';

  export let name;
  export let path;
  let updating = false;
  let originalText = '';
  let configText = '';

  onMount(reload);

  function clear() {
    configText = '';
  }

  function openEditor() {
    textAreaModal(name, configText, function(updatedText) {
      configText = updatedText;
      save();
    });
  }

  function reload() {
    updating = true;
    fetch($instance.url + path, newGetRequest())
      .then(function(response) {
        if (response.status === 404) return '';
        if (!response.ok) throw new Error('Status: ' + response.status);
        return response.text();
      })
      .then(function(text) {
        originalText = text;
        configText = text;
      })
      .catch(function(error) { notifyError('Failed to load ' + name); })
      .finally(function() { updating = false; });
  }

  function save() {
    updating = true;
    let request = newPostRequest('text/plain');
    request.body = configText;
    fetch($instance.url + path, request)
      .then(function(response) {
        if (!response.ok) throw new Error('Status: ' + response.status);
        originalText = configText;
        notifyInfo(name + ' saved.');
      })
      .catch(function(error) { notifyError('Failed to update ' + name); })
      .finally(function() { updating = false; });
  }
</script>


<div class="block">
  <div class="field">
    <label for={'configFileText' + name.replaceAll(' ', '')} class="label">
      <a href={$instance.url + path} target="_blank">{name}</a>
    </label>
    <slot />
    <div class="control pr-6">
      <textarea id={'configFileText' + name.replaceAll(' ', '')} class="textarea is-family-monospace is-size-7"
                bind:value={configText}></textarea>
    </div>
  </div>
  <div class="field">
    <div class="control buttons">
      <button disabled={updating} on:click={openEditor}
              name="editor" class="button">&nbsp;<i class="fa fa-expand-arrows-alt"></i>&nbsp;</button>
      <button disabled={updating || !configText} on:click={clear}
              name="clear" class="button is-danger">Clear</button>
      <button disabled={updating} on:click={reload}
              name="reload" class="button is-warning">Reload</button>
      <button disabled={updating || originalText === configText} on:click={save}
              name="save" class="button is-primary">Save</button>
    </div>
  </div>
</div>
