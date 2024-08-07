<script>
  import { onMount, getContext } from 'svelte';
  import { notifyInfo, notifyError } from '$lib/util/notifications';
  import { textAreaModal } from '$lib/modal/modals';
  import { newPostRequest, newGetRequest } from '$lib/util/sjgmsapi';
  import ExtLink from '$lib/widget/ExtLink.svelte';

  const instance = getContext('instance');
  const serverStatus = getContext('serverStatus');
  const eventStarted = getContext('eventStarted');
  const eventEndMaint = getContext('eventEndMaint');

  export let name;
  export let path;

  let configFileTextId = 'configFileText' + name.replaceAll(' ', '');
  let processing = true;
  let originalText = '';
  let configText = '';

  $: cannotAction = processing || $serverStatus.state === 'MAINTENANCE';
  $: cannotEdit = cannotAction;
  $: cannotClear = cannotAction || !configText;
  $: cannotReload = cannotAction;
  $: cannotSave = cannotAction || originalText === configText;

  $: if (($eventStarted || $eventEndMaint) && !originalText && !configText) {
    reload();
  }

  function reload() {
    processing = true;
    fetch(instance.url(path), newGetRequest())
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
      .finally(function() { processing = false; });
  }

  function editor() {
    textAreaModal(name, configText, function(updatedText) {
      configText = updatedText;
      save();
    });
  }

  function clear() {
    configText = '';
  }

  function save() {
    processing = true;
    const request = newPostRequest('text/plain');
    request.body = configText;
    fetch(instance.url(path), request)
      .then(function(response) {
        if (!response.ok) throw new Error('Status: ' + response.status);
        originalText = configText;
        notifyInfo(name + ' saved.');
      })
      .catch(function(error) { notifyError('Failed to update ' + name); })
      .finally(function() { processing = false; });
  }

  onMount(reload);
</script>


<div class="block">
  <div class="field">
    <label for={configFileTextId} class="label">
      <ExtLink href={instance.url(path)}>{name}&nbsp;</ExtLink>
    </label>
    {#if $$slots.default}
      <div class="content mb-2"><slot /></div>
    {/if}
    <div class="control pr-6">
      <textarea id={configFileTextId} class="textarea is-family-monospace is-size-7" spellcheck="false"
                disabled={cannotEdit} bind:value={configText}></textarea>
    </div>
  </div>
  <div class="field">
    <div class="control buttons">
      <button disabled={cannotEdit} on:click={editor} name="editor" title="Editor" class="button">
        <i class="fa fa-expand-arrows-alt fa-lg"></i>&nbsp;&nbsp;Editor</button>
      <button disabled={cannotClear} on:click={clear} name="clear" title="Clear" class="button is-danger">
        <i class="fa fa-eraser fa-lg"></i>&nbsp;&nbsp;Clear</button>
      <button disabled={cannotReload} on:click={reload} name="reload" title="Reload" class="button is-warning">
        <i class="fa fa-rotate-right fa-lg"></i>&nbsp;&nbsp;Reload</button>
      <button disabled={cannotSave} on:click={save} name="save" title="Save" class="button is-primary">
        <i class="fa fa-floppy-disk fa-lg"></i>&nbsp;&nbsp;Save</button>
    </div>
  </div>
</div>
