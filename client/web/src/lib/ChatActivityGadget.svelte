<script>
  import QueryCriteriaContext from '$lib/QueryCriteriaContext.svelte';
  import QueryDateRange from '$lib/QueryDateRange.svelte';
  import QueryExecute from '$lib/QueryExecute.svelte';
  import ChatActivity from '$lib/ChatActivity.svelte';
</script>


<QueryCriteriaContext>
  <QueryDateRange defaultFromMillis="21600000" />
  <QueryExecute />
  <ChatActivity />
</QueryCriteriaContext>
