<script>
  import { onMount, onDestroy } from 'svelte';
  import { notifyError } from '$lib/notifications';
  import { sleep, capitalize, humanFileSize, humanDuration } from '$lib/util';
  import { baseurl, newGetRequest } from '$lib/serverjockeyapi';
  import RubiksCube from '$lib/RubiksCube.svelte';

  let looping = true;
  let info = {
    version: '', os: '', uptime: 0, cpu: { percent: 0 },
    memory: { total: 0, used: 0, available: 0, free: 0, percent: 0.0 },
    disk: { total: 0, used: 0, free: 0, percent: 0.0 },
    net: { local: '', public: '' }
  };

  async function updateSystemInfo() {
    while (looping) {
      await fetch(baseurl + '/system/info', newGetRequest())
        .then(function(response) {
          if (!response.ok) throw new Error('Status: ' + response.status);
          return response.json();
        })
        .then(function(json) {
          if (looping) { info = json; }
        })
        .catch(function(error) {
          looping = false;
          notifyError('Failed to load System Info.');
        });
      if (looping) { await sleep(20000); }
    }
  };

  onMount(updateSystemInfo);
  onDestroy(function() { looping = false; });
</script>


<div class="columns">
  <div class="column is-one-third">
    <div class="pl-5 pr-6"><RubiksCube /></div>
  </div>
  <div class="column is-one-third">
    <table class="table is-thinner">
      <tbody>
        <tr><td class="has-text-weight-bold">Version</td><td>{info.version}</td></tr>
        <tr><td class="has-text-weight-bold">OS</td><td>{info.os}</td></tr>
        <tr><td class="has-text-weight-bold">CPU</td><td>{info.cpu.percent}%</td></tr>
        <tr><td class="has-text-weight-bold">Memory</td><td></td></tr>
        <tr><td>Total</td><td>{humanFileSize(info.memory.total)}</td></tr>
        <tr><td>Used</td><td>{humanFileSize(info.memory.used)}</td></tr>
        <tr><td>Available</td><td>{humanFileSize(info.memory.available)}</td></tr>
        <tr><td>Free</td><td>{humanFileSize(info.memory.free)}</td></tr>
        <tr><td>Usage</td><td>{info.memory.percent}%</td></tr>
      </tbody>
    </table>
  </div>
  <div class="column is-one-third">
    <table class="table is-thinner">
      <tbody>
        <tr><td class="has-text-weight-bold">Uptime</td><td>{humanDuration(info.uptime)}</td></tr>
        <tr><td class="has-text-weight-bold">Disk</td><td></td></tr>
        <tr><td>Total</td><td>{humanFileSize(info.disk.total)}</td></tr>
        <tr><td>Used</td><td>{humanFileSize(info.disk.used)}</td></tr>
        <tr><td>Available</td><td>{humanFileSize(info.disk.free)}</td></tr>
        <tr><td>Usage</td><td>{info.disk.percent}%</td></tr>
        <tr><td class="has-text-weight-bold">IPv4</td><td></td></tr>
        <tr><td>Local</td><td>{info.net.local}</td></tr>
        <tr><td>Public</td><td>{info.net.public}</td></tr>
      </tbody>
    </table>
  </div>
</div>
