<script>
  import { onMount, getContext } from 'svelte';
  import { confirmModal } from '$lib/modal/modals';
  import { notifyInfo, notifyWarning, notifyError } from '$lib/util/notifications';
  import { isString, guessTextFile, humanFileSize, toCamelCase } from '$lib/util/util';
  import { newGetRequest, newPostRequest } from '$lib/util/sjgmsapi';
  import SpinnerIcon from '$lib/widget/SpinnerIcon.svelte';

  const instance = getContext('instance');
  const serverStatus = getContext('serverStatus');
  const eventDown = getContext('eventDown');
  const eventStarted = getContext('eventStarted');
  const eventEndMaint = getContext('eventEndMaint');
  const [softLimit, hardLimit] = [50, 300];

  export let rootPath;
  export let allowDelete = 0;  // 0=Never 1=!RunOrMaint 2=!Maint 3=Always
  export let confirmDelete = true;
  export let sorter = null;
  export let columnsMeta = { type: true, date: 'Date', name: 'Name', size: 'Size' };
  export let customMeta = null;

  const idPrefix = 'fileSystem' + toCamelCase(rootPath.replaceAll('/', ' '));

  let pwdUrl = null;
  let notifyText = null;
  let loading = true;
  let loadingError = false;
  let paths = [];
  let hasActions = allowDelete > 0 || customMeta;
  let columnCount = (hasActions ? 1 : 0) + (columnsMeta.type ? 1 : 0) + (columnsMeta.date ? 1 : 0)
                  + (columnsMeta.name ? 1 : 0) + (columnsMeta.size ? 1 : 0);

  $: isMaint = $serverStatus.state === 'MAINTENANCE';
  $: cannotAction = $serverStatus.running || isMaint;
  $: cannotDelete = (allowDelete === 1 && cannotAction) || (allowDelete === 2 && isMaint);
  $: containerClass = paths.length > softLimit ? 'block oversize-container mr-6' : 'block';

  $: if (!cannotAction && notifyText) {
    notifyInfo(notifyText);
    notifyText = null;
  }

  $: if ($eventDown || $eventStarted || $eventEndMaint) {
    reload();
  }

  function rootUrl() {
    return instance.url(rootPath);
  }

  function urlToPath(url) {
    if (!url) return 'UNKNOWN';
    return url.substring(rootUrl().length);
  }

  function defaultSorter(a, b) {
    const typeCompare = b.type.localeCompare(a.type);
    if (typeCompare != 0) return typeCompare;
    return b.mtime - a.mtime;
  }

  function load(url) {
    loading = true;
    loadingError = false;
    if (!url) { url = rootUrl(); }
    if (!pwdUrl) { pwdUrl = url; }
    fetch(url, newGetRequest())
      .then(function(response) {
        if (!response.ok) throw new Error('Status: ' + response.status);
        return response.json();
      })
      .then(function(json) {
        json.sort(sorter ? sorter : defaultSorter);
        if (json.length > hardLimit) { notifyWarning('Only ' + hardLimit + ' of ' + json.length + ' entries shown'); }
        paths = json.slice(0, hardLimit);
        pwdUrl = url;
      })
      .catch(function(error) {
        if (url === rootUrl()) {
          loadingError = true;
          pwdUrl = rootUrl();
          paths = [];
          notifyError('Failed to load ' + rootPath);
        } else {
          loadRoot();
        }
      })
      .finally(function() {
        loading = false;
      });
  }

  export function reload() {
    load(pwdUrl);
  }

  function loadRoot() {
    load(rootUrl());
  }

  function upDirectory() {
    const parts = pwdUrl.split('/');
    parts.pop();
    load(parts.join('/'));
  }

  function customAction(url) {
    customMeta.action(
      urlToPath(url),
      { // callbacks
        start: function() {
          isMaint = true;
          return true;
        },
        started: function(text) {
          notifyText = text;
        },
        error: function(text) {
          isMaint = false;
          notifyError(text);
          return false;
        }
      });
  }

  function deleteAction(url) {
    if (confirmDelete) {
      confirmModal('Delete?\n' + urlToPath(url), function() {
        deleteUrl(url);
      });
    } else {
      deleteUrl(url);
    }
  }

  function deleteUrl(url) {
    fetch(url, newPostRequest())
      .then(function(response) { if (!response.ok) throw new Error('Status: ' + response.status); })
      .catch(function(error) { notifyError('Failed to delete ' + urlToPath(url)); })
      .finally(reload);
  }

  onMount(loadRoot);
</script>


<div class={containerClass}><div>
  <table class="table">
    <thead>
      <tr>
        {#if columnsMeta.type}<th>{isString(columnsMeta.type) ? columnsMeta.type : ''}</th>{/if}
        {#if columnsMeta.date}<th>{isString(columnsMeta.date) ? columnsMeta.date : ''}</th>{/if}
        {#if columnsMeta.name}<th>{isString(columnsMeta.name) ? columnsMeta.name : ''}</th>{/if}
        {#if columnsMeta.size}<th>{isString(columnsMeta.size) ? columnsMeta.size : ''}</th>{/if}
        {#if hasActions}<th></th>{/if}
      </tr>
    </thead>
    <tbody id="{idPrefix}Files">
      {#if pwdUrl && pwdUrl != rootUrl()}
        <tr>
          <td colspan={columnCount}>
            <button id="{idPrefix}LoadRoot" title="ROOT" class="button mr-2 mb-1" on:click={loadRoot}>
              &nbsp;<i class="fa fa-angles-up fa-lg"></i>&nbsp;</button>
            <button id="{idPrefix}UpDirectory" title="UP" class="button" on:click={upDirectory}>
              <i class="fa fa-turn-down fa-lg rotate-180"></i>&nbsp;&nbsp;&nbsp;{urlToPath(pwdUrl)}</button>
          </td>
        </tr>
      {/if}
      {#if paths.length === 0}
        <tr><td colspan={columnCount}>
          {#if loadingError}
            <i class="fa fa-triangle-exclamation fa-lg mr-1"></i> Error loading files
          {:else}
            {#if loading}
              <SpinnerIcon /> Loading...
            {:else}
              <i class="fa fa-diamond fa-lg mr-1"></i> No files found
            {/if}
          {/if}
        </td></tr>
      {:else}
        {#each paths as path}
          <tr>
            {#if columnsMeta.type}
              <td>
                {#if path.type === 'directory'}
                  <i class="fa fa-folder fa-2x fileico"></i>
                {/if}
                {#if path.type === 'file'}
                  <i class="fa {guessTextFile(path.name) ? 'fa-file-lines' : 'fa-file'} fa-2x fileico"></i>
                {/if}
              </td>
            {/if}
            {#if columnsMeta.date}
              <td class="notranslate">{path.updated}</td>
            {/if}
            {#if columnsMeta.name && path.type === 'directory'}
              <td class="word-break-all notranslate" colspan={columnsMeta.size ? 2 : 1}>
                <a href={'#'} on:click|preventDefault={function() { load(path.url); }}>{path.name}</a>
              </td>
            {/if}
            {#if columnsMeta.name && path.type === 'file'}
              <td class="word-break-all notranslate">
                <a href={path.url} target={guessTextFile(path.name) ? '_blank' : '_self'}>{path.name}</a>
              </td>
              {#if columnsMeta.size}
                <td class="notranslate">{humanFileSize(path.size)}</td>
              {/if}
            {/if}
            {#if hasActions}
              <td>
                {#if customMeta}
                  <button name="{idPrefix}ActionE{path.name}" title={customMeta.name}
                          disabled={cannotAction || path.type === 'directory'}
                          class={'button ' + customMeta.button + (allowDelete > 0 ? ' mb-1' : '')}
                          on:click={function() { customAction(path.url); }}>
                    <i class="fa {customMeta.icon} fa-lg"></i></button>
                {/if}
                {#if allowDelete > 0}
                  <button name="{idPrefix}DeleteE{path.name}" title="Delete"
                          disabled={cannotDelete} class="button is-danger"
                          on:click={function() { deleteAction(path.url); }}>
                    <i class="fa fa-trash-can fa-lg"></i></button>
                {/if}
              </td>
            {/if}
          </tr>
        {/each}
      {/if}
    </tbody>
  </table>
</div></div>


<style>
  .oversize-container {
    max-height: 480px;
    resize: vertical;
    overflow: auto;
  }

  .oversize-container div {
    min-width: 380px;
  }

  .fileico {
    width: 0.6em;
  }
</style>
