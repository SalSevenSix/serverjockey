<script>
  import { onMount } from 'svelte';
  import { confirmModal } from '$lib/modals';
  import { notifyInfo, notifyWarning, notifyError } from '$lib/notifications';
  import { isString, guessTextFile, humanFileSize } from '$lib/util';
  import { newGetRequest, newPostRequest } from '$lib/sjgmsapi';
  import { instance, serverStatus, eventDown, eventStarted, eventEndMaint } from '$lib/instancestores';
  import Spinner from '$lib/Spinner.svelte';

  export let rootPath;
  export let allowDelete = 0;  // 0=Never 1=!RunOrMaint 2=!Maint 3=Always
  export let confirmDelete = true;
  export let sorter = null;
  export let columnsMeta = { type: true, date: 'Date', name: 'Name', size: 'Size' };
  export let customMeta = null;

  let root = null;
  let pwd = null;
  let notifyText = null;
  let loading = true;
  let paths = [];
  let hasActions = allowDelete > 0 || customMeta;
  let columnCount = (hasActions ? 1 : 0) + (columnsMeta.type ? 1 : 0) + (columnsMeta.date ? 1 : 0)
                  + (columnsMeta.name ? 1 : 0) + (columnsMeta.size ? 1 : 0);

  $: isMaint = $serverStatus.state === 'MAINTENANCE';
  $: cannotAction = $serverStatus.running || isMaint;
  $: cannotDelete = (allowDelete === 1 && cannotAction) || (allowDelete === 2 && isMaint);

  $: if (!cannotAction && notifyText) {
    notifyInfo(notifyText);
    notifyText = null;
  }

  $: if ($eventDown || $eventStarted || $eventEndMaint) {
    reload();
  }

  function defaultSorter(a, b) {
    let typeCompare = b.type.localeCompare(a.type);
    if (typeCompare != 0) return typeCompare;
    return b.mtime - a.mtime;
  }

  function load(url) {
    loading = true;
    fetch(url, newGetRequest())
      .then(function(response) {
        if (!response.ok) throw new Error('Status: ' + response.status);
        return response.json();
      })
      .then(function(json) {
        json.sort(sorter ? sorter : defaultSorter);
        if (json.length > 60) { notifyWarning('Only 60 of ' + json.length + ' entries shown'); }
        paths = json.slice(0, 60);
        pwd = url;
      })
      .catch(function(error) {
        if (url === root) {
          paths = [];  // TODO maybe add single error entry
          pwd = root;
          notifyError('Failed to load ' + rootPath);
        } else {
          rootDirectory();
        }
      })
      .finally(function() {
        loading = false;
      });
  }

  export function reload() {
    load(pwd);
  }

  function rootDirectory() {
    load(root);
  }

  function upDirectory() {
    let parts = pwd.split('/');
    parts.pop();
    load(parts.join('/'));
  }

  function customAction(url) {
    customMeta.action(
      url.substring(root.length),
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
      confirmModal('Delete?\n' + url.substring(root.length), function() {
        deleteUrl(url);
      });
    } else {
      deleteUrl(url);
    }
  }

  function deleteUrl(url) {
    fetch(url, newPostRequest())
      .then(function(response) { if (!response.ok) throw new Error('Status: ' + response.status); })
      .catch(function(error) { notifyError('Failed to delete ' + url.substring(root.length)); })
      .finally(reload);
  }

  onMount(function() {
    root = $instance.url + rootPath;
    pwd = root;
    rootDirectory();
  });
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
              &nbsp;<i class="fa fa-angles-up fa-lg"></i>&nbsp;</button>
            <button name="up" class="button" title="UP" on:click={upDirectory}>
              <i class="fa fa-turn-down fa-lg"></i>&nbsp;&nbsp;&nbsp;{pwd.substring(root.length)}</button>
          </td>
        </tr>
      {/if}
      {#if paths.length === 0}
        <tr><td colspan={columnCount}>
          {#if loading}
            <Spinner clazz="fa fa-spinner fa-lg mr-1" /> Loading...
          {:else}
            <i class="fa fa-diamond fa-lg mr-1"></i> No files found
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
              <td>{path.updated}</td>
            {/if}
            {#if columnsMeta.name && path.type === 'directory'}
              <td class="word-break-all" colspan={columnsMeta.size ? 2 : 1}>
                <a href={'#'} on:click|preventDefault={function() { load(path.url); }}>{path.name}</a>
              </td>
            {/if}
            {#if columnsMeta.name && path.type === 'file'}
              <td class="word-break-all">
                <a href={path.url} target={guessTextFile(path.name) ? '_blank' : '_self'}>{path.name}</a>
              </td>
              {#if columnsMeta.size}
                <td>{humanFileSize(path.size)}</td>
              {/if}
            {/if}
            {#if hasActions}
              <td>
                {#if customMeta}
                  <button name={customMeta.name} title={customMeta.name}
                          disabled={cannotAction || path.type === 'directory'}
                          class={'button ' + customMeta.button + (allowDelete > 0 ? ' mb-1' : '')}
                          on:click={function() { customAction(path.url); }}>
                    <i class="fa {customMeta.icon} fa-lg"></i></button>
                {/if}
                {#if allowDelete > 0}
                  <button name="Delete" title="Delete" disabled={cannotDelete} class="button is-danger"
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

  .fa-turn-down {
    transform: rotate(180deg);
  }
</style>
