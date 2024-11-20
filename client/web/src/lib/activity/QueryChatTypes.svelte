<script>
  import { getContext } from 'svelte';
  import InputRadio from '$lib/widget/InputRadio.svelte';

  const query = getContext('query');

  let type = 'chat';

  query.criteria.chat = function() {
    return { type: type };
  }
</script>


<div class="block">
  <p class="has-text-weight-bold mb-1" title="Choose what results to include">Include</p>
  <InputRadio id="queryChatTypes{query.contextId}" name="chattype" bind:group={type} width="6.5em" options={[
     {value: 'chat', title: 'Player chat messages'},
     {value: 'session', title: 'Player login events'},
     {value: 'both', title: 'Both Chat and Session'}]} />
</div>
