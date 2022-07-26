<script>
  import { onMount } from 'svelte';
	import { humanFileSize } from '$lib/util';
	import { instance, newGetRequest } from '$lib/serverjockeyapi';

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
	  pwd = parts.join('/');
	  update(pwd);
  }

	function openDirectory() {
	  update(this.name);
  }

	async function update(url) {
	  paths = await fetch(url, newGetRequest())
      .then(function(response) {
        if (!response.ok) throw new Error('Status: ' + response.status);
        return response.json();
      })
      .catch(function(error) {
        if (url === root) {
          alert(error);
        } else {
          update(root);
        }
      });
      pwd = url;
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
      .catch(function(error) { update(root); });
  }
</script>


<div class="block">
  <table class="table">
    <thead>
      <tr>
        <th>Type</th>
        <th>File</th>
        <th>Size</th>
      </tr>
    </thead>
    <tbody>
      {#if pwd != root}
        <tr>
          <td><a href="#" on:click|preventDefault={upDirectory}>[ROOT]</a></td>
          <td><a href="#" on:click|preventDefault={upDirectory}>[UP]</a></td>
          <td></td>
        </tr>
      {/if}
      {#each paths as path}
        <tr>
          <td>{path.type}</td>
          {#if path.type === 'directory'}
            <td><a href="#" name="{path.url}" on:click|preventDefault={openDirectory}>{path.name}</a></td>
          {/if}
          {#if path.type === 'file'}
            <td><a href="#" name="{path.url}" on:click|preventDefault={openFile}>{path.name}</a></td>
          {/if}
          <td>{humanFileSize(path.size)}</td>
        </tr>
      {/each}
    </tbody>
  </table>
</div>
