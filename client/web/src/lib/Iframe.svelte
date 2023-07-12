<script>
  import { onMount } from 'svelte';
  import { serverStatus } from '$lib/instancestores';

  let baseurl = '';
  onMount(function() {
    baseurl = 'http://' + window.location.hostname;
  });

  $: url = baseurl + ':' + $serverStatus.details.cport;
  $: showConsole = url.startsWith('http') && $serverStatus.state === 'STARTED';
</script>


<div class="block">
  {#if showConsole}
    <p class="pl-2">
      <a href={url} target="_blank">Open console in new tab &nbsp;<i class="fa fa-up-right-from-square"></i></a>
    </p>
    <iframe src={url} title="Console Commands"></iframe>
  {:else}
    <p class="pl-2">
      <i class="fa fa-triangle-exclamation fa-lg"></i>
      Console Unavailable. Server not STARTED.
    </p>
  {/if}
</div>


<style>
  iframe {
    width: 100%;
    height: 400px;
    border: none;
  }
</style>
