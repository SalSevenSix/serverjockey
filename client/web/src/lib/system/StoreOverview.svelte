<script>
  import Collapsible from '$lib/widget/Collapsible.svelte';
  import CheckStore from '$lib/system/CheckStore.svelte';
  import StoreActions from '$lib/system/StoreActions.svelte';
  import QueryCriteriaContext from '$lib/activity/QueryCriteriaContext.svelte';
  import QueryChooseInstance from '$lib/activity/QueryChooseInstance.svelte';
  import QueryDateRange from '$lib/activity/QueryDateRange.svelte';
  import InstanceActivity from '$lib/activity/InstanceActivity.svelte';
  import PlayerActivity from '$lib/activity/PlayerActivity.svelte';
</script>


<CheckStore>
  <Collapsible icon="fa-chart-pie" title="Instance Activity">
    <QueryCriteriaContext contextId="InstanceActivity">
      <QueryChooseInstance />
      <QueryDateRange defaultFromMillis="2592000000" headless />
      <InstanceActivity />
    </QueryCriteriaContext>
  </Collapsible>
  <Collapsible icon="fa-user-clock" title="Player Activity">
    <QueryCriteriaContext contextId="PlayerActivity">
      <QueryChooseInstance />
      <QueryDateRange defaultFromMillis="2592000000" headless />
      <PlayerActivity />
    </QueryCriteriaContext>
  </Collapsible>
  <Collapsible icon="fa-database" title="Store Actions">
    <StoreActions />
  </Collapsible>
</CheckStore>
