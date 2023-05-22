<script>
  import { serverStatus } from '$lib/serverjockeyapi';
</script>


{#if $serverStatus.running}
  <i class="fa fa-toggle-on ss-running fa-lg"></i>
{:else}
  <i class="fa {$serverStatus.state === 'MAINTENANCE' ? 'fa-toggle-on ss-maint' : 'fa-toggle-off'} fa-lg"></i>
{/if}


<style>
  .ss-running {
    color: #48C78E;
  }
  .ss-maint {
    color: #F14668;
  }
</style>
