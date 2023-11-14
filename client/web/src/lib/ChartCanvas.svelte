<script>
  import { onMount } from 'svelte';
  import Chart from 'chart.js/auto';

  export let data;

  let chartCanvas;

  onMount(function() {
    new Chart(chartCanvas, data);
  });
</script>


<canvas bind:this={chartCanvas}></canvas>
