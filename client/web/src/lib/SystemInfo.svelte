<script>
  import { onMount } from 'svelte';
  import { notifyError } from '$lib/notifications';
	import { capitalize, humanFileSize, humanDuration } from '$lib/util';
	import { baseurl, newGetRequest } from '$lib/serverjockeyapi';

  let info = {
    version: '0.0.0',
    uptime: 0,
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

	onMount(function() {
	  fetch(baseurl + '/system/info', newGetRequest())
      .then(function(response) {
        if (!response.ok) throw new Error('Status: ' + response.status);
        return response.json();
      })
      .then(function(json) { info = json; })
      .catch(function(error) { notifyError('Failed to load System Info.'); });
  });
</script>


<div class="columns">
  <div class="column">
    <figure class="pl-5 pr-6"><img src="/assets/rubiks-cube-white.svg" alt="Banner" /></figure>
  </div>
  <div class="column is-one-quarter">
    <table class="table">
      <tbody>
        <tr><td class="has-text-weight-bold">Version</td><td>{info.version}</td></tr>
        <tr><td class="has-text-weight-bold">Memory</td><td></td></tr>
        <tr><td>Total</td><td>{humanFileSize(info.memory.total)}</td></tr>
        <tr><td>Used</td><td>{humanFileSize(info.memory.used)}</td></tr>
        <tr><td>Available</td><td>{humanFileSize(info.memory.available)}</td></tr>
        <tr><td>Free</td><td>{humanFileSize(info.memory.free)}</td></tr>
        <tr><td>Usage</td><td>{info.memory.percent}%</td></tr>
      </tbody>
    </table>
  </div>
  <div class="column">
    <table class="table">
      <tbody>
        <tr><td class="has-text-weight-bold">Uptime</td><td>{humanDuration(info.uptime)}</td></tr>
        <tr><td class="has-text-weight-bold">CPU</td><td>{info.cpu.percent}%</td></tr>
        <tr><td class="has-text-weight-bold">Disk</td><td></td></tr>
        <tr><td>Total</td><td>{humanFileSize(info.disk.total)}</td></tr>
        <tr><td>Used</td><td>{humanFileSize(info.disk.used)}</td></tr>
        <tr><td>Available</td><td>{humanFileSize(info.disk.free)}</td></tr>
        <tr><td>Usage</td><td>{info.disk.percent}%</td></tr>
      </tbody>
    </table>
  </div>
</div>
