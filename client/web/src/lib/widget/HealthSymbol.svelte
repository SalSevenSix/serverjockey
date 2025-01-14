<script>
  export let red = 0.9;
  export let amber = 0.5;
  export let value = null;

  $: [icon, status] = valueUpdated(value); function valueUpdated(current) {
    let result = ['fa-circle', 'status-color-green'];
    if (current > amber) { result[1] = 'status-color-amber'; }
    if (current > red) { result = ['fa-circle-exclamation', 'status-color-red']; }
    return result;
  }
</script>


{#if value != null}
  <i class="fa {icon} {status}"></i>&nbsp;
{/if}
