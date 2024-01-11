<script>
  import Collapsible from '$lib/Collapsible.svelte';
  import CheckStore from '$lib/CheckStore.svelte';
  import QueryCriteriaContext from '$lib/QueryCriteriaContext.svelte';
  import QueryChooseInstance from '$lib/QueryChooseInstance.svelte';
  import QueryDateRange from '$lib/QueryDateRange.svelte';
  import QuerySearchText from '$lib/QuerySearchText.svelte';
  import QueryChatTypes from '$lib/QueryChatTypes.svelte';
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
      <div class="columns">
        <div class="column">
          <QuerySearchText name="Search for Player" title="Search for a Player by name"
                           placeholder="literal or regexp using '/'" />
        </div>
        <div class="column">
          <QueryChatTypes />
        </div>
      </div>
      <QueryExecute />
      <ChatActivity />
    </QueryCriteriaContext>
  </Collapsible>
</CheckStore>
