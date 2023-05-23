<script>
  import { onMount } from 'svelte';
  import { notifyError } from '$lib/notifications';
  import { confirmModal } from '$lib/modals';
  import { humanFileSize } from '$lib/util';
  import { instance, serverStatus, newGetRequest, newPostRequest } from '$lib/serverjockeyapi';

  export let allowDelete = false;
  export let sortFunction = function(a, b) {
      let typeCompare = b.type.localeCompare(a.type);
      if (typeCompare != 0) return typeCompare;
      return b.name.localeCompare(a.name);
    };

  let reloading = true;
  let root = $instance.url + '/logs';
  let pwd = root;
  let paths = [];

  let lastRunning = $serverStatus.running;
  $: serverRunningChange($serverStatus.running);
  function serverRunningChange(running) {
    if (lastRunning === true && running === false) {
      reload(pwd);
    }
    lastRunning = running;
  }

  let lastState = $serverStatus.state;
  $: serverStateChange($serverStatus.state);
  function serverStateChange(serverState) {
    if (lastState != 'STARTED' && serverState === 'STARTED') {
      reload(pwd);
    }
    lastState = serverState;
  }

  onMount(rootDirectory);

  function rootDirectory() {
    reload(root);
  }

  function upDirectory() {
    let parts = pwd.split('/');
    parts.pop();
    reload(parts.join('/'));
  }

  function reload(url) {
    reloading = true;
    fetch(url, newGetRequest())
      .then(function(response) {
        if (!response.ok) throw new Error('Status: ' + response.status);
        return response.json();
      }).then(function(json) {
        json.sort(sortFunction);
        paths = json;
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

  function openDirectory() {
    reload(this.name);
  }

  function deletePath() {
    let url = this.name;
    let path = url.substring(root.length);
    confirmModal('Delete this file or folder?\n' + path, function() {
      fetch(url, newPostRequest())
        .then(function(response) { if (!response.ok) throw new Error('Status: ' + response.status); })
        .catch(function(error) { notifyError('Failed to delete ' + path); })
        .finally(function() { reload(pwd); });
    });
  }
</script>


<div class="block">
  <table class="table">
    <thead>
      <tr>
        <th>Type</th>
        <th>File</th>
        <th>Size</th>
        {#if allowDelete}<th></th>{/if}
      </tr>
    </thead>
    <tbody>
      {#if pwd != root}
        <tr>
          <td>
            <button name="root" class="button" title="ROOT" on:click={rootDirectory}>
              &nbsp;<i class="fa fa-angle-double-up fa-lg"></i>&nbsp;</button>
          </td>
          <td colspan={allowDelete ? '3' : '2'}>
            <button name="up" class="button" title="UP" on:click={upDirectory}>
              &nbsp;<i class="fa fa-level-up-alt fa-lg"></i>&nbsp;&nbsp;{pwd.substring(root.length)}</button>
          </td>
        </tr>
      {/if}
      {#if paths.length === 0}
        <tr><td colspan={allowDelete ? '4' : '3'}>
          {reloading ? 'Loading...' : 'No Logs found.'}
        </td></tr>
      {:else}
        {#each paths as path}
          <tr>
            {#if path.type === 'directory'}
              <td><i class="fa fa-folder fa-2x"></i></td>
              <td colspan="2" class="word-break-all">
                <a href={'#'} name="{path.url}" on:click|preventDefault={openDirectory}>{path.name}</a></td>
            {/if}
            {#if path.type === 'file'}
              <td><i class="fa fa-file-alt fa-2x"></i></td>
              <td class="word-break-all"><a href={path.url} target="_blank">{path.name}</a></td>
              <td>{humanFileSize(path.size)}</td>
            {/if}
            {#if allowDelete}
              <td>
                <button name="{path.url}" class="button is-danger" title="Delete"
                        disabled={$serverStatus.running} on:click={deletePath}>
                  <i class="fa fa-trash-can fa-lg"></i></button>
              </td>
            {/if}
          </tr>
        {/each}
      {/if}
    </tbody>
  </table>
</div>
