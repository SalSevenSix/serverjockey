<script>
  import { onMount, onDestroy } from 'svelte';
  import { sleep } from '$lib/util';

  export let clazz = 'fa fa-arrows-spin fa-lg';
  export let increment = 5;
  export let delay = 50;

  let spinning = true;
  let current = 0;

  onMount(async function() {
    increment = parseInt(increment);
    delay = parseInt(delay);
    while (spinning) {
      current += increment;
      if (current >= 360) { current = 0; }
      await sleep(delay);
    }
  });

  onDestroy(function() {
    spinning = false;
  });
</script>


<i class={clazz} style:transform=rotate({current}deg)></i>
