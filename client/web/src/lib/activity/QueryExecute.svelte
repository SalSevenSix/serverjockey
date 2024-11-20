<script>
  import { getContext } from 'svelte';

  export let buttonName = 'Search';

  const query = getContext('query');
  const blocker = query.blocker;
</script>


<div class="block buttons mr-6 pl-6 pr-6">
  <button id="queryExecute{query.contextId}" title={buttonName} class="button is-primary is-fullwidth"
          disabled={$blocker} on:click={query.execute}>
    <i class="fa fa-magnifying-glass fa-lg"></i>&nbsp; {buttonName}</button>
</div>
