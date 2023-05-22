<script>
  import { onMount } from 'svelte';
  import { notifyInfo, notifyError } from '$lib/notifications';
  import { textAreaModal } from '$lib/modals';
  import { instance, newPostRequest, newGetRequest } from '$lib/serverjockeyapi';

  export let name;
  export let path;
  let configFileTextId = 'configFileText' + name.replaceAll(' ', '');
  let updating = true;
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
    <label for={configFileTextId} class="label">
      <a href={$instance.url + path} target="_blank">{name}</a>
    </label>
    <slot />
    <div class="control pr-6">
      <textarea id={configFileTextId} class="textarea is-family-monospace is-size-7"
                disabled={updating} bind:value={configText}></textarea>
    </div>
  </div>
  <div class="field">
    <div class="control buttons">
      <button disabled={updating} on:click={openEditor} name="editor" title="Editor" class="button">
        <i class="fa fa-expand-arrows-alt"></i>&nbsp;&nbsp;Editor</button>
      <button disabled={updating || !configText} on:click={clear} name="clear" title="Clear" class="button is-danger">
        <i class="fa fa-eraser"></i>&nbsp;&nbsp;Clear</button>
      <button disabled={updating} on:click={reload} name="reload" title="Reload" class="button is-warning">
        <i class="fa fa-rotate-right"></i>&nbsp;&nbsp;Reload</button>
      <button disabled={updating || originalText === configText} on:click={save}
              name="save" title="Save" class="button is-primary">
        <i class="fa fa-floppy-disk fa-lg"></i>&nbsp;&nbsp;Save</button>
    </div>
  </div>
</div>
