<script>
  import { getContext } from 'svelte';

  export let buttonName = 'Search';

  const query = getContext('query');
  const blocker = query.blocker;
</script>


<div class="block buttons">
  <button class="button is-primary is-fullwidth" name="queryexecute" title={buttonName}
          disabled={$blocker} on:click={query.execute}>
    <i class="fa fa-magnifying-glass fa-lg"></i>&nbsp; {buttonName}</button>
</div>
