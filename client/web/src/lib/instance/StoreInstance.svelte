<script>
  import Collapsible from '$lib/widget/Collapsible.svelte';
  import CheckStore from '$lib/system/CheckStore.svelte';
  import QueryCriteriaContext from '$lib/activity/QueryCriteriaContext.svelte';
  import QueryChooseInstance from '$lib/activity/QueryChooseInstance.svelte';
  import QueryDateRange from '$lib/activity/QueryDateRange.svelte';
  import QuerySearchText from '$lib/activity/QuerySearchText.svelte';
  import QueryChatTypes from '$lib/activity/QueryChatTypes.svelte';
  import QueryExecute from '$lib/activity/QueryExecute.svelte';
  import InstanceActivity from '$lib/activity/InstanceActivity.svelte';
  import PlayerActivity from '$lib/activity/PlayerActivity.svelte';
  import ChatActivity from '$lib/activity/ChatActivity.svelte';
</script>


<CheckStore>
  <Collapsible icon="fa-chart-pie" title="Activity">
    <QueryCriteriaContext contextId="Activity">
      <QueryChooseInstance />
      <QueryDateRange defaultFromMillis="2592000000" />
      <QueryExecute />
      <InstanceActivity />
      <PlayerActivity />
    </QueryCriteriaContext>
  </Collapsible>
  <Collapsible icon="fa-comments" title="Chat Log">
    <QueryCriteriaContext contextId="ChatLog">
      <QueryChooseInstance />
      <QueryDateRange defaultFromMillis="21600000" />
      <div class="columns">
        <div class="column">
          <QuerySearchText label="Search for Player" title="Search for a Player by name"
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
