<script>
  import Collapsible from '$lib/widget/Collapsible.svelte';
  import HttpsControls from '$lib/system/HttpsControls.svelte';
</script>


<Collapsible icon="fa-gears" title="System">
  <div class="columns">
    <div class="column is-one-quarter">
      <a href="/system/log" title="Open" target="_blank">
        &nbsp; View Log &nbsp;<i class="fa fa-up-right-from-square fa-lg"></i></a>
    </div>
    <div class="column is-three-quarters">
      Open system log in a new tab.
    </div>
  </div>
  <HttpsControls />
</Collapsible>
