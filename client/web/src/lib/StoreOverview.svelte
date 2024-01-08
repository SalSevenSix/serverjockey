<script>
  import Collapsible from '$lib/Collapsible.svelte';
  import CheckStore from '$lib/CheckStore.svelte';
  import QueryCriteriaContext from '$lib/QueryCriteriaContext.svelte';
  import QueryChooseInstance from '$lib/QueryChooseInstance.svelte';
  import QueryDateRange from '$lib/QueryDateRange.svelte';
  import InstanceActivity from '$lib/InstanceActivity.svelte';
  import PlayerActivity from '$lib/PlayerActivity.svelte';
  import StoreActions from '$lib/StoreActions.svelte';
</script>


<CheckStore>
  <Collapsible icon="fa-chart-pie" title="Instance Activity">
    <QueryCriteriaContext>
      <QueryChooseInstance />
      <QueryDateRange defaultFromMillis="2592000000" headless />
      <InstanceActivity />
    </QueryCriteriaContext>
  </Collapsible>
  <Collapsible icon="fa-user-clock" title="Player Activity">
    <QueryCriteriaContext>
      <QueryChooseInstance />
      <QueryDateRange defaultFromMillis="2592000000" headless />
      <PlayerActivity />
    </QueryCriteriaContext>
  </Collapsible>
  <Collapsible icon="fa-database" title="Store Actions">
    <StoreActions />
  </Collapsible>
</CheckStore>
