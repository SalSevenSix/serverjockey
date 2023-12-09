<script>
  import { connection } from '$lib/sjgmsapi';

  export let disconnect;
</script>


<div>
  <p>
    <button class="process" on:click={disconnect}>Disconnect</button>&nbsp;
    <a title="Open ServerJockey in new tab" href={$connection.url} target="_blank">{$connection.url}</a>
  </p>
</div>
