<script>
  import { onDestroy } from 'svelte';
  import { shortISODateTimeString, humanDuration } from 'common/util/util';

  let { meta } = $props();
  let duration = $state(Date.now() - meta.updated);

  function tick() { duration = Date.now() - meta.updated; }

  const timer = setInterval(tick, 1000);
  onDestroy(function() { clearInterval(timer); });
</script>


<div class="dashpanel font-monospace text-align-center"><p>
  updated {shortISODateTimeString(meta.updated)}<br>
  [&nbsp;{humanDuration(duration, 'ms', 2)} ago&nbsp;]</p>
</div>
