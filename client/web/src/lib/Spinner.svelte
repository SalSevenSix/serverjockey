<script>
  import { onMount, onDestroy } from 'svelte';

  export let clazz = 'fa fa-spinner fa-lg';
  export let increment = 5;
  export let delay = 50;

  let clock = null;
  let current = 0;

  onMount(function() {
    increment = parseInt(increment);
    delay = parseInt(delay);
    clock = setInterval(function() {
      current += increment;
      if (current >= 360) { current = 0; }
    }, delay);
  });

  onDestroy(function() {
    if (clock) { clearInterval(clock); }
  });
</script>


<i class={clazz} style:transform=rotate({current}deg)></i>
