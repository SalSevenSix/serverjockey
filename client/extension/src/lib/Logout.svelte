<script>
  import { connection } from '$lib/sjgmsapi';

  export let disconnect;
</script>


<div>
  <p class="white-space-nowrap">
    <button id="logoutDisconnect" class="process" on:click={disconnect}>Disconnect</button>&nbsp;
    <a id="logoutOpenServerJockey" title="Open ServerJockey in new tab"
       href={$connection.url} target="_blank">{$connection.url}</a>
  </p>
</div>
