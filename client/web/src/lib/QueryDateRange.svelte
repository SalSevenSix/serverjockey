<script>
  import { getContext } from 'svelte';

  const query = getContext('query');
  const atfromOptions = { '': 'None',
    '3600000': '1 hour', '10800000': '3 hours', '21600000': '6 hours', '43200000': '12 hours',
    '86400000': '24 hours', '604800000': '7 days', '1209600000': '14 days',
    '2592000000': '30 days', '5184000000': '60 days', '7776000000': '90 days'};

  export let defaultFromMillis = '2592000000';

  let atfrom = '';
  let atto = '';
  let atfromMillis = defaultFromMillis;
  let attoNow = true;

  query.criteria.atrange = function() {
    let result = { atfrom: null, atto: null };
    if (atto) { result.atto = atto; }
    if (attoNow) { result.atto = Date.now().toString(); }
    if (atfrom) { result.atfrom = atfrom; }
    if (atfromMillis) { result.atfrom = (parseInt(result.atto) - parseInt(atfromMillis)).toString(); }
    return result;
  };
</script>


<div class="block">
  <div class="field">
    <label for="querydaterangeatfrom" class="label" title="atfrom">atfrom</label>
    <div class="control">
      <input id="querydaterangeatfrom" class="input" type="text" bind:value={atfrom}>
    </div>
  </div>
  <div class="field">
    <label for="querydaterangeatto" class="label" title="atto">atto</label>
    <div class="control">
      <input id="querydaterangeatto" class="input" type="text" bind:value={atto}>
    </div>
  </div>
</div>
