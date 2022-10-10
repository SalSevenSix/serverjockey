<script>
  import { onMount } from 'svelte';
  import { serverStatus } from '$lib/serverjockeyapi';

  let baseurl = 'http://localhost'
  $: url = baseurl + ':' + $serverStatus.details.cport;

  onMount(function() {
    baseurl = 'http://' + window.location.hostname;
  });
</script>


<div class="content">
  {#if $serverStatus.state === 'STARTED'}
    <p><a href={url} target="_blank">Open in new tab</a></p>
    <iframe src={url} title="Console Commands"></iframe>
  {:else}
    <p>Console Unavailable. Server not STARTED.</p>
  {/if}
</div>


<style>
  iframe {
    width: 100%;
    height: 300px;
    border: none;
  }
</style>
