<script>
  import { onMount } from 'svelte';
	import { capitalize, humanFileSize } from '$lib/util';
	import { baseurl, newGetRequest } from '$lib/serverjockeyapi';

  let systemLoad = {
    cpu: {
      percent: 0
    },
    memory: {
      total: 0,
      used: 0,
      available: 0,
      free: 0,
      percent: 0.0
    },
    disk: {
      total: 0,
      used: 0,
      free: 0,
      percent: 0.0
    }
  };

	onMount(async function() {
	  /*
	  systemLoad = await fetch(baseurl + '/system/load', newGetRequest())
      .then(function(response) {
        if (!response.ok) throw new Error('Status: ' + response.status);
        return response.json();
      })
      .catch(function(error) { alert('Error: ' + error); });
    */
  });

</script>


<div class="columns">
  <div class="column">
    <figure class="pl-5 pr-6"><img src="/assets/cube-ornate.svg" alt="Banner Image" /></figure>
  </div>
  <div class="column is-one-quarter">
    <table class="table">
      <tbody>
        <tr><td class="has-text-weight-bold">CPU</td><td></td></tr>
        <tr><td>Percent</td><td>{systemLoad.cpu.percent}</td></tr>
        <tr><td class="has-text-weight-bold">Disk</td><td></td></tr>
        <tr><td>Total</td><td>{humanFileSize(systemLoad.disk.total)}</td></tr>
        <tr><td>Used</td><td>{humanFileSize(systemLoad.disk.used)}</td></tr>
        <tr><td>Available</td><td>{humanFileSize(systemLoad.disk.free)}</td></tr>
        <tr><td>Percent</td><td>{systemLoad.disk.percent}</td></tr>
      </tbody>
    </table>
  </div>
  <div class="column">
    <table class="table">
      <tbody>
        <tr><td class="has-text-weight-bold">Memory</td><td></td></tr>
        <tr><td>Total</td><td>{humanFileSize(systemLoad.memory.total)}</td></tr>
        <tr><td>Used</td><td>{humanFileSize(systemLoad.memory.used)}</td></tr>
        <tr><td>Available</td><td>{humanFileSize(systemLoad.memory.available)}</td></tr>
        <tr><td>Free</td><td>{humanFileSize(systemLoad.memory.free)}</td></tr>
        <tr><td>Percent</td><td>{systemLoad.memory.percent}</td></tr>
      </tbody>
    </table>
  </div>
</div>
