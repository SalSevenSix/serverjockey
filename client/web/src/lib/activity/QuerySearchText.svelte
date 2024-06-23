<script>
  import { getContext } from 'svelte';
  import { generateId } from '$lib/util/util';
  import InputText from '$lib/widget/InputText.svelte';

  const query = getContext('query');
  const inputId = 'querySearchText' + generateId();

  export let key = 'search';
  export let name = 'Search';
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


<div class="block">
  <InputText id={inputId} name={name} bind:value={text} title={title}
             onKeypress={kpExecute} placeholder={placeholder} />
</div>
