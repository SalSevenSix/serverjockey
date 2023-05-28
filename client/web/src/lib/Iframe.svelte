<script>
  import { onMount } from 'svelte';
  import { serverStatus } from '$lib/sjgmsapi';

  let baseurl = '';
  onMount(function() {
    baseurl = 'http://' + window.location.hostname;
  });

  $: url = baseurl + ':' + $serverStatus.details.cport;
  $: showConsole = url.startsWith('http') && $serverStatus.state === 'STARTED';
</script>


<div class="content">
  {#if showConsole}
    <p>
      <a href={url} target="_blank">Open console in new tab &nbsp;<i class="fa fa-up-right-from-square"></i></a>
    </p>
    <iframe src={url} title="Console Commands"></iframe>
  {:else}
    <p>
      <i class="fa fa-triangle-exclamation fa-lg"></i>
      Console Unavailable. Server not STARTED.
    </p>
  {/if}
</div>


<style>
  iframe {
    width: 100%;
    height: 300px;
    border: none;
  }
</style>
