<script>
  import { shortISODateTimeString } from 'common/util/util';
  import ChartCanvas from '$lib/ChartCanvas.svelte';

  let { data } = $props();

  function chartDataIntervals(entry) {
    const [labels, sessions, played, max] = [{}, [], [], []];
    entry.intervals.data.forEach(function(interval) {
      const dts = shortISODateTimeString(interval.atfrom);
      const label = entry.intervals.hours > 1 ? dts.substring(5, 10) : dts.substring(11, 16);
      labels[label] = interval.atfrom;
      sessions.push(interval.sessions);
      played.push(interval.uptime / 3600000);
      max.push(interval.max);
    });
    return {
      type: 'line',
      data: {
        labels: Object.keys(labels),
        datasets: [{ label: 'player hours', data: played },
                   { label: 'concurrent', data: max },
                   { label: 'sessions', data: sessions }]
      }
    };
  }
</script>


<div id="PlayerChart" class="dashcontainer"><div class="dashpanel">
  <div><ChartCanvas data={chartDataIntervals(data.p.results)} /></div>
</div></div>
