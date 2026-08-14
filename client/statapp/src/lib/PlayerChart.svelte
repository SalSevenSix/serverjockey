<script>
  import { shortISODateTimeString } from 'common/util/util';
  import ChartCanvas from '$lib/ChartCanvas.svelte';

  let { data } = $props();

  function chartDataIntervals(entry) {
    const data = { labels: {}, sessions: [], played: [], max: [] };
    entry.intervals.data.forEach(function(interval) {
      const dts = shortISODateTimeString(interval.atfrom);
      const label = entry.intervals.hours > 1 ? dts.substring(5, 10) : dts.substring(11, 16);
      data.labels[label] = interval.atfrom;
      data.sessions.push(interval.sessions);
      data.played.push(interval.uptime / 3600000);
      data.max.push(interval.max);
    });
    return {
      type: 'line',
      data: {
        labels: Object.keys(data.labels),
        datasets: [{ label: 'player hours', data: data.played },
                   { label: 'concurrent', data: data.max },
                   { label: 'sessions', data: data.sessions }]
      }
    };
  }
</script>


<div id="PlayerChart" style="width: 50%">
  <ChartCanvas data={chartDataIntervals(data.p.results)} />
</div>
