<script>
  import { onMount, getContext } from 'svelte';
  import { toCamelCase } from '$lib/util/util';
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

  const idPrefix = 'configFile' + toCamelCase(name);

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
      .catch(function() { notifyError('Failed to load ' + name); })
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
      .catch(function() { notifyError('Failed to update ' + name); })
      .finally(function() { processing = false; });
  }

  onMount(reload);
</script>


<div class="block">
  <div class="field">
    <label for="{idPrefix}Text" class="label">
      <ExtLink href={instance.url(path)}>{name}&nbsp;</ExtLink>
    </label>
    {#if $$slots.default}
      <div class="content mb-2"><slot /></div>
    {/if}
    <div class="control pr-6">
      <textarea id="{idPrefix}Text" class="textarea is-family-monospace is-size-7" spellcheck="false"
                disabled={cannotEdit} bind:value={configText}></textarea>
    </div>
  </div>
  <div class="field">
    <div class="control buttons">
      <button id="{idPrefix}Editor" title="Editor" class="button" disabled={cannotEdit} on:click={editor}>
        <i class="fa fa-expand-arrows-alt fa-lg"></i>&nbsp;&nbsp;Editor</button>
      <button id="{idPrefix}Clear" title="Clear" class="button is-danger" disabled={cannotClear} on:click={clear}>
        <i class="fa fa-eraser fa-lg"></i>&nbsp;&nbsp;Clear</button>
      <button id="{idPrefix}Reload" title="Reload" class="button is-warning" disabled={cannotReload} on:click={reload}>
        <i class="fa fa-rotate-right fa-lg"></i>&nbsp;&nbsp;Reload</button>
      <button id="{idPrefix}Save" title="Save" class="button is-primary" disabled={cannotSave} on:click={save}>
        <i class="fa fa-floppy-disk fa-lg"></i>&nbsp;&nbsp;Save</button>
    </div>
  </div>
</div>


<style>
  .button {
    min-width: 7em;
  }
</style>
