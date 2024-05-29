<script>
  export let red = 0.9;
  export let amber = 0.5;
  export let value = null;

  $: icon = value > red ? 'fa-circle-exclamation' : 'fa-circle';
  $: status = value > amber ? value > red ? 'status-color-red' : 'status-color-amber' : 'status-color-green';
</script>


{#if value != null}
  <i class="fa {icon} {status}"></i>&nbsp;
{/if}
