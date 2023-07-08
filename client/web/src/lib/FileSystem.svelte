<script>
  import { onMount } from 'svelte';
  import { notifyInfo, notifyWarning, notifyError } from '$lib/notifications';
  import { isString, guessTextFile, humanFileSize } from '$lib/util';
  import { instance, serverStatus, eventDown, eventStarted, newGetRequest, newPostRequest } from '$lib/sjgmsapi';

  export let rootPath;
  export let allowDelete = false;
  export let customMeta = null;
  export let columnsMeta = { type: true, date: 'Date', name: 'Name', size: 'Size' };
  export let sorter = null;

  let root = $instance.url + rootPath;
  let pwd = root;
  let hasActions = allowDelete || customMeta;
  let columnCount = (hasActions ? 1 : 0) + (columnsMeta.type ? 1 : 0) + (columnsMeta.date ? 1 : 0)
                  + (columnsMeta.name ? 1 : 0) + (columnsMeta.size ? 1 : 0);

  $: cannotAction = $serverStatus.running || $serverStatus.state === 'MAINTENANCE';

  let notifyText = null;
  $: if (!cannotAction && notifyText) {
    notifyInfo(notifyText);
    notifyText = null;
  }

  $: if ($eventDown || $eventStarted) {
    reload(pwd);
  }

  function defaultSorter(a, b) {
    let typeCompare = b.type.localeCompare(a.type);
    if (typeCompare != 0) return typeCompare;
    return b.mtime - a.mtime;
  }

  let reloading = true;
  let paths = [];
  function reload(url) {
    reloading = true;
    fetch(url, newGetRequest())
      .then(function(response) {
        if (!response.ok) throw new Error('Status: ' + response.status);
        return response.json();
      }).then(function(json) {
        json.sort(sorter ? sorter : defaultSorter);
        if (json.length > 60) { notifyWarning('Only 60 of ' + json.length + ' entries shown'); }
        paths = json.slice(0, 60);
        pwd = url;
      })
      .catch(function(error) {
        if (url === root) {
          paths = [];
          pwd = root;
        } else {
          rootDirectory();
        }
      })
      .finally(function() {
        reloading = false;
      });
  }

  function rootDirectory() {
    reload(root);
  }

  function openDirectory() {
    reload(this.name);
  }

  function upDirectory() {
    let parts = pwd.split('/');
    parts.pop();
    reload(parts.join('/'));
  }

  function customAction(url) {
    customMeta.action(url,
      function() { cannotAction = true; },
      function(text) { notifyText = text; });
  }

  function deleteAction(url) {
    fetch(url, newPostRequest())
      .then(function(response) { if (!response.ok) throw new Error('Status: ' + response.status); })
      .catch(function(error) { notifyError('Failed to delete ' + url.substring(root.length)); })
      .finally(function() { reload(pwd); });
  }

  onMount(rootDirectory);
</script>


<div class="block">
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
    <tbody>
      {#if pwd != root}
        <tr>
          <td colspan={columnCount}>
            <button name="root" class="button mr-2 mb-1" title="ROOT" on:click={rootDirectory}>
              &nbsp;<i class="fa fa-angle-double-up fa-lg"></i>&nbsp;</button>
            <button name="up" class="button" title="UP" on:click={upDirectory}>
              &nbsp;<i class="fa fa-level-up-alt fa-lg"></i>&nbsp;&nbsp;{pwd.substring(root.length)}</button>
          </td>
        </tr>
      {/if}
      {#if paths.length === 0}
        <tr><td colspan={columnCount}>
          {reloading ? 'Loading...' : 'No files found.'}
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
              <td>{path.updated}</td>
            {/if}
            {#if columnsMeta.name && path.type === 'directory'}
              <td class="word-break-all" colspan={columnsMeta.size ? 2 : 1}>
                <a href={'#'} name={path.url} on:click|preventDefault={openDirectory}>{path.name}</a>
              </td>
            {/if}
            {#if columnsMeta.name && path.type === 'file'}
              <td class="word-break-all">
                <a href={path.url} name={path.name} target={guessTextFile(path.name) ? '_blank' : '_self'}>
                  {path.name}</a>
              </td>
              {#if columnsMeta.size}
                <td>{humanFileSize(path.size)}</td>
              {/if}
            {/if}
            {#if hasActions}
              <td>
                {#if customMeta}
                  <button name={customMeta.name} title={customMeta.name} disabled={cannotAction}
                          class={'button ' + customMeta.button + (allowDelete ? ' mb-1' : '')}
                          on:click={function() { customAction(path.url); }}>
                    <i class="fa {customMeta.icon} fa-lg"></i></button>
                {/if}
                {#if allowDelete}
                  <button name="Delete" title="Delete" disabled={cannotAction}
                          class="button is-danger"
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
</div>


<style>
  .fileico {
    width: 0.6em;
  }
</style>
