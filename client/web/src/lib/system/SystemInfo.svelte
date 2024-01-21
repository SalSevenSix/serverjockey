<script>
  import { onMount, onDestroy } from 'svelte';
  import { notifyError } from '$lib/util/notifications';
  import { sleep, humanFileSize, humanDuration } from '$lib/util/util';
  import { newGetRequest } from '$lib/util/sjgmsapi';
  import RubiksCube from '$lib/widget/RubiksCube.svelte';
  import SpinnerOverlay from '$lib/widget/SpinnerOverlay.svelte';

  let looping = true;
  let info = null;

  function osIcon(osPrettyName) {
    let parts = osPrettyName.split(' ');
    return 'fa-' + parts[0].toLowerCase();
  }

  onMount(async function() {
    while (looping) {
      await fetch('/system/info', newGetRequest())
        .then(function(response) {
          if (!response.ok) throw new Error('Status: ' + response.status);
          return response.json();
        })
        .then(function(json) {
          if (looping) { info = json; }
        })
        .catch(function(error) {
          notifyError('Failed to load System Info.');
        });
      if (looping) { await sleep(32000); }
    }
  });

  onDestroy(function() { looping = false; });
</script>


<div class="columns">
  <div class="column is-one-third content mb-0">
    <figure class="image max-400"><RubiksCube /></figure>
  </div>
  <div class="column is-one-third position-relative">
    {#if !info}<SpinnerOverlay />{/if}
    <table class="table is-thinner">
      {#if info}
        <tbody>
          <tr><td class="field-column has-text-weight-bold">Version</td><td>{info.version}</td></tr>
          <tr><td class="field-column has-text-weight-bold">OS</td>
              <td><i class="fa-brands {osIcon(info.os)}"></i> {info.os}</td></tr>
          <tr><td class="field-column has-text-weight-bold">CPU</td><td>{info.cpu.percent}%</td></tr>
          <tr><td class="field-column has-text-weight-bold">Memory</td><td></td></tr>
          <tr><td class="field-column">Total</td><td>{humanFileSize(info.memory.total)}</td></tr>
          <tr><td class="field-column">Used</td><td>{humanFileSize(info.memory.used)}</td></tr>
          <tr><td class="field-column">Available</td><td>{humanFileSize(info.memory.available)}</td></tr>
          <tr><td class="field-column">Free</td><td>{humanFileSize(info.memory.free)}</td></tr>
          <tr><td class="field-column">Usage</td><td>{info.memory.percent}%</td></tr>
        </tbody>
      {:else}
        <tbody>
          <tr><td class="has-text-weight-bold">Version</td><td>...</td></tr>
          <tr><td class="has-text-weight-bold">OS</td><td>...</td></tr>
          <tr><td class="has-text-weight-bold">CPU</td><td>...</td></tr>
          <tr><td class="has-text-weight-bold">Memory</td><td>...</td></tr>
          <tr><td>Total</td><td>...</td></tr>
          <tr><td>Used</td><td>...</td></tr>
          <tr><td>Available</td><td>...</td></tr>
          <tr><td>Free</td><td>...</td></tr>
          <tr><td>Usage</td><td>...</td></tr>
        </tbody>
      {/if}
    </table>
  </div>
  <div class="column is-one-third position-relative">
    {#if !info}<SpinnerOverlay />{/if}
    <table class="table is-thinner">
      {#if info}
        <tbody>
          <tr><td class="field-column has-text-weight-bold">Uptime</td><td>{humanDuration(info.uptime)}</td></tr>
          <tr><td class="field-column has-text-weight-bold">Disk</td><td></td></tr>
          <tr><td class="field-column">Total</td><td>{humanFileSize(info.disk.total)}</td></tr>
          <tr><td class="field-column">Used</td><td>{humanFileSize(info.disk.used)}</td></tr>
          <tr><td class="field-column">Available</td><td>{humanFileSize(info.disk.free)}</td></tr>
          <tr><td class="field-column">Usage</td><td>{info.disk.percent}%</td></tr>
          <tr><td class="field-column has-text-weight-bold">IPv4</td><td></td></tr>
          <tr><td class="field-column">Local</td><td>{info.net.local}</td></tr>
          <tr><td class="field-column">Public</td><td>{info.net.public}</td></tr>
        </tbody>
      {:else}
        <tbody>
          <tr><td class="has-text-weight-bold">Uptime</td><td>...</td></tr>
          <tr><td class="has-text-weight-bold">Disk</td><td>...</td></tr>
          <tr><td>Total</td><td>...</td></tr>
          <tr><td>Used</td><td>...</td></tr>
          <tr><td>Available</td><td>...</td></tr>
          <tr><td>Usage</td><td>...</td></tr>
          <tr><td class="has-text-weight-bold">IPv4</td><td>...</td></tr>
          <tr><td>Local</td><td>...</td></tr>
          <tr><td>Public</td><td>...</td></tr>
        </tbody>
      {/if}
    </table>
  </div>
</div>


<style>
  .field-column {
    width: 33%;
  }
</style>