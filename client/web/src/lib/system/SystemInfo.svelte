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
          <tr><td class="field-column has-text-weight-bold" title="ServerJockey version">
            Version</td><td class="notranslate">{info.version}</td></tr>
          <tr><td class="field-column has-text-weight-bold" title="ServerJockey uptime">
            Uptime</td><td class="notranslate">{humanDuration(info.uptime)}</td></tr>
          <tr><td class="field-column has-text-weight-bold" title="Operating system name">
            OS</td><td class="notranslate"><i class="fa-brands {osIcon(info.os)}"></i> {info.os}</td></tr>
          <tr><td class="field-column has-text-weight-bold" title="Disk usage">
            Disk</td><td class="notranslate">{info.disk.percent}%</td></tr>
          <tr><td class="field-column" title="Total disk size">
            Total</td><td class="notranslate">{humanFileSize(info.disk.total)}</td></tr>
          <tr><td class="field-column" title="Used disk space">
            Used</td><td class="notranslate">{humanFileSize(info.disk.used)}</td></tr>
          <tr><td class="field-column" title="Available disk space">
            Available</td><td class="notranslate">{humanFileSize(info.disk.free)}</td></tr>
          <tr><td class="field-column has-text-weight-bold" title="Public (internet) IPv4 address">
            IPv4</td><td class="notranslate">{info.net.public}</td></tr>
          <tr><td class="field-column" title="Local (LAN) IPv4 address">
            Local</td><td class="notranslate">{info.net.local}</td></tr>
        </tbody>
      {:else}
        <tbody>
          <tr><td class="has-text-weight-bold">Version</td><td>...</td></tr>
          <tr><td class="has-text-weight-bold">Uptime</td><td>...</td></tr>
          <tr><td class="has-text-weight-bold">OS</td><td>...</td></tr>
          <tr><td class="has-text-weight-bold">Disk</td><td>...</td></tr>
          <tr><td>Total</td><td>...</td></tr>
          <tr><td>Used</td><td>...</td></tr>
          <tr><td>Available</td><td>...</td></tr>
          <tr><td class="has-text-weight-bold">IPv4</td><td>...</td></tr>
          <tr><td>Local</td><td>...</td></tr>
        </tbody>
      {/if}
    </table>
  </div>
  <div class="column is-one-third position-relative">
    {#if !info}<SpinnerOverlay />{/if}
    <table class="table is-thinner">
      {#if info}
        <tbody>
          <tr><td class="field-column has-text-weight-bold" title="CPU usage">
            CPU</td><td class="notranslate">{info.cpu.percent}%</td></tr>
          <tr><td class="field-column" title="CPU model name">
            Model</td><td class="notranslate">{info.cpu.modelname}</td></tr>
          <tr><td class="field-column notranslate" title="CPU Architecture | Cores | Threads">
            A | C | T</td><td class="notranslate">{info.cpu.arch} | {info.cpu.cpus} | {info.cpu.threads}</td></tr>
          <tr><td class="field-column has-text-weight-bold" title="Memory usage">
            Memory</td><td class="notranslate">{info.memory.percent}%</td></tr>
          <tr><td class="field-column" title="Total memory size">
            Total</td><td class="notranslate">{humanFileSize(info.memory.total)}</td></tr>
          <tr><td class="field-column" title="Used memory space">
            Used</td><td class="notranslate">{humanFileSize(info.memory.used)}</td></tr>
          <tr><td class="field-column" title="Available memory space">
            Available</td><td class="notranslate">{humanFileSize(info.memory.available)}</td></tr>
          <tr><td class="field-column" title="Total swap size">
            Swap</td><td class="notranslate">{humanFileSize(info.memory.swap)}</td></tr>
        </tbody>
      {:else}
        <tbody>
          <tr><td class="has-text-weight-bold">CPU</td><td>...</td></tr>
          <tr><td>Model</td><td>...</td></tr>
          <tr><td class="notranslate">A | C | T</td><td>...</td></tr>
          <tr><td class="has-text-weight-bold">Memory</td><td>...</td></tr>
          <tr><td>Total</td><td>...</td></tr>
          <tr><td>Used</td><td>...</td></tr>
          <tr><td>Available</td><td>...</td></tr>
          <tr><td>Swap</td><td>...</td></tr>
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
