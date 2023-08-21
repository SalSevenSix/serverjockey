<script>
  import { onDestroy } from 'svelte';
  import { humanDuration } from '$lib/util';

  let uptimeClock = null;
  let uptimeNow = 0;

  export function setUptime(uptime) {
    if (uptime) {
      uptimeNow = uptime;
      if (!uptimeClock) {
        uptimeClock = setInterval(function() { uptimeNow += 10000; }, 10000);
      }
    } else {
      stopUptimeClock();
      uptimeNow = 0;
    }
  }

  function stopUptimeClock() {
    if (!uptimeClock) return;
    clearInterval(uptimeClock);
    uptimeClock = null;
  }

  onDestroy(stopUptimeClock);
</script>


{#if uptimeNow}{humanDuration(uptimeNow)}{/if}
