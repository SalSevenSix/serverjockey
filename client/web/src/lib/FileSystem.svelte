<script>
  import { onMount } from 'svelte';
  import { notifyError } from '$lib/notifications';
  import { confirmModal } from '$lib/modals';
	import { humanFileSize } from '$lib/util';
	import { instance, serverStatus, newGetRequest, newPostRequest } from '$lib/serverjockeyapi';

  export let allowDelete = false;

  let root = $instance.url + '/logs';
  let pwd = root;
  let paths = [];

	onMount(rootDirectory);

	function rootDirectory() {
	  update(root);
  }

	function upDirectory() {
	  let parts = pwd.split('/');
	  parts.pop();
	  update(parts.join('/'));
  }

	function update(url) {
	  fetch(url, newGetRequest())
      .then(function(response) {
        if (!response.ok) throw new Error('Status: ' + response.status);
        return response.json();
      }).then(function(json) {
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
      });
  }

	function openDirectory() {
	  update(this.name);
  }

	function openFile() {
    fetch(this.name, newGetRequest())
      .then(function(response) {
        if (!response.ok) throw new Error('Status: ' + response.status);
        return response.blob();
      })
      .then(function(blob) {
        window.open(window.URL.createObjectURL(blob)).focus();
      })
      .catch(function(error) { rootDirectory(); });
  }

  function deletePath() {
    let url = this.name;
    let path = url.substring(root.length);
    confirmModal('Delete this folder or file?\n' + path, function() {
      fetch(url, newPostRequest())
        .then(function(response) { if (!response.ok) throw new Error('Status: ' + response.status); })
        .catch(function(error) { notifyError('Failed to delete ' + path); })
        .finally(function() { update(pwd); });
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
      {#if pwd === root && paths.length === 0}
        <tr>
          <td></td>
          <td><button name="reload" class="button is-small" on:click={rootDirectory}>RELOAD</button></td>
          <td></td>
          {#if allowDelete}<td></td>{/if}
        </tr>
      {/if}
      {#if pwd != root}
        <tr>
          <td><button name="root" class="button is-small" on:click={rootDirectory}>ROOT</button></td>
          <td><button name="up" class="button is-small" on:click={upDirectory}>UP</button> {pwd.substring(root.length)}</td>
          <td></td>
          {#if allowDelete}<td></td>{/if}
        </tr>
      {/if}
      {#each paths as path}
        <tr>
          <td>{path.type === 'file' ? 'file' : 'dir'}</td>
          {#if path.type === 'directory'}
            <td><a href={'#'} name="{path.url}" on:click|preventDefault={openDirectory}>{path.name}</a></td>
          {/if}
          {#if path.type === 'file'}
            <td><a href={'#'} name="{path.url}" on:click|preventDefault={openFile}>{path.name}</a></td>
          {/if}
          <td>{humanFileSize(path.size)}</td>
          {#if allowDelete}
            <td class="buttons">
              <button disabled={$serverStatus.running} name="{path.url}" class="button is-danger" on:click={deletePath}>Delete</button>
            </td>
          {/if}
        </tr>
      {/each}
    </tbody>
  </table>
</div>
