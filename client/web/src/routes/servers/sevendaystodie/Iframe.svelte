<script>
  import { onMount, getContext } from 'svelte';
  import ExtLink from '$lib/widget/ExtLink.svelte';

  const serverStatus = getContext('serverStatus');

  let baseurl = '';

  $: url = baseurl + ':' + $serverStatus.details.cport;
  $: showConsole = url.startsWith('http') && $serverStatus.state === 'STARTED';

  onMount(function() {
    baseurl = 'http://' + window.location.hostname;
  });
</script>


<div class="block">
  {#if showConsole}
    <p class="pl-2">
      <ExtLink href={url}>Open console in new tab&nbsp;</ExtLink>
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
