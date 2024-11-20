<script>
  import { getContext } from 'svelte';
  import InputText from '$lib/widget/InputText.svelte';

  const query = getContext('query');

  export let key = 'search';
  export let label = 'Search';
  export let title = null;
  export let placeholder = null;

  let text = '';

  function kpExecute(event) {
    if (event.key === 'Enter') { query.execute(); }
  }

  query.criteria[key] = function() {
    return { text: text };
  }
</script>


<div class="block mr-5">
  <InputText id="querySearchText{query.contextId}" label={label} title={title}
             bind:value={text} onKeypress={kpExecute} placeholder={placeholder} />
</div>
