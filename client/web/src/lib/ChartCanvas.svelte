<script>
  import Chart from 'chart.js/auto';
  import { onMount } from 'svelte';

  export let data;

  let chartCanvas;

  onMount(function() {
    new Chart(chartCanvas, data);
  });
</script>


<canvas bind:this={chartCanvas}></canvas>
