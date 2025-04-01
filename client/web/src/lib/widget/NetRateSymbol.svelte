<script>
  export let icon;
  export let value = null;

  $: [normal, high] = valueUpdated(value); function valueUpdated(current) {
    if (!current || current === '0 B/s') return [false, false];
    if (current.endsWith(' B/s') || current.endsWith(' KiB/s')) return [true, false];
    return [false, true];
  }
</script>


<i class="fa {icon}" class:status-color-green={normal} class:status-color-amber={high}></i>&nbsp;
