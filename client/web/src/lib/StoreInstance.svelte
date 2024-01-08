<script>
  import Collapsible from '$lib/Collapsible.svelte';
  import CheckStore from '$lib/CheckStore.svelte';
  import QueryCriteriaContext from '$lib/QueryCriteriaContext.svelte';
  import QueryChooseInstance from '$lib/QueryChooseInstance.svelte';
  import QueryDateRange from '$lib/QueryDateRange.svelte';
  import QueryExecute from '$lib/QueryExecute.svelte';
  import InstanceActivity from '$lib/InstanceActivity.svelte';
  import PlayerActivity from '$lib/PlayerActivity.svelte';
  import ChatActivity from '$lib/ChatActivity.svelte';
</script>


<CheckStore>
  <Collapsible icon="fa-chart-pie" title="Activity">
    <QueryCriteriaContext>
      <QueryChooseInstance />
      <QueryDateRange defaultFromMillis="2592000000" />
      <QueryExecute />
      <InstanceActivity />
      <PlayerActivity />
    </QueryCriteriaContext>
  </Collapsible>
  <Collapsible icon="fa-comments" title="Chat Log">
    <QueryCriteriaContext>
      <QueryChooseInstance />
      <QueryDateRange defaultFromMillis="21600000" />
      <QueryExecute />
      <ChatActivity />
    </QueryCriteriaContext>
  </Collapsible>
</CheckStore>
