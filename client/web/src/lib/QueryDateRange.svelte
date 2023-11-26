<script>
  import { getContext, tick } from 'svelte';
  import { DateInput } from 'date-picker-svelte'  // https://date-picker-svelte.kasper.space/docs
  import { generateId } from '$lib/util';

  const query = getContext('query');
  const minDate = new Date(946684800000);  // 2000-01-01 00:00:00
  const randomId = generateId();
  const attoId = 'atto' + randomId;
  const attoNowId = 'attonow' + randomId;
  const atfromId = 'atfrom' + randomId;
  const atfromMillisId = 'atfrommillis' + randomId;
  const atfromOptions = { '0': ' ---',
    '3600000': '1 hour', '10800000': '3 hours', '21600000': '6 hours', '43200000': '12 hours',
    '86400000': '24 hours', '604800000': '7 days', '1209600000': '14 days',
    '2592000000': '30 days', '5184000000': '60 days', '7776000000': '90 days' };

  export let defaultFromMillis = '2592000000';

  let atfrom = null;
  let atfromValid = false;
  let atto = null;
  let attoValid = false;
  let attoNow = true;
  let atfromMillis = defaultFromMillis;

  $: if (attoNow) { atto = null; } else { focusElement(attoId); }
  $: hasAtfromMillis = atfromMillis != '0';
  $: if (hasAtfromMillis) { atfrom = null; } else { focusElement(atfromId); }
  $: valid = validate(atfrom, atto, attoNow, atfromMillis);
  $: query.blocker.notify('QueryDateRangeInvalid', !valid);

  function focusElement(elementId) {
    tick().then(function() { document.getElementById(elementId).focus(); });
  }

  function validate() {
    if (atfrom && !atfromValid) return false;
    if (atto && !attoValid) return false;
    let resolvable = (attoNow || atto) && (hasAtfromMillis || atfrom);
    if (!resolvable) return false;
    let millis = resolveRange();
    if (millis.atfrom > millis.atto) return false;
    return true;
  }

  function resolveRange() {
    let millis = { atfrom: null, atto: null };
    if (atto) { millis.atto = atto.getTime(); }
    if (attoNow) { millis.atto = Date.now(); }
    if (atfrom) { millis.atfrom = atfrom.getTime(); }
    if (hasAtfromMillis) { millis.atfrom = millis.atto - parseInt(atfromMillis); }
    return millis;
  }

  query.criteria.atrange = function() {
    let millis = resolveRange();
    return { atfrom: millis.atfrom.toString(), atto: millis.atto.toString() };
  }
</script>


<div class="columns">
  <div class="column">
    <div class="columns">
      <div class="column is-7">
        <div class="field">
          <label for={atfromId} class="label" title="Begin date and time for search range">Date From</label>
          <DateInput id={atfromId} timePrecision="second" placeholder=" ---" min={minDate}
                     bind:disabled={hasAtfromMillis} bind:valid={atfromValid} bind:value={atfrom} />
        </div>
      </div>
      <div class="column is-5">
        <div class="field">
          <label for={atfromMillisId} class="label" title="use preset range previous to Date To">or previous</label>
          <div class="control select">
            <select id={atfromMillisId} bind:value={atfromMillis}>
              {#each Object.keys(atfromOptions) as key}
                <option value={key}>{atfromOptions[key]}</option>
              {/each}
            </select>
          </div>
        </div>
      </div>
    </div>
  </div>
  <div class="column">
    <div class="columns">
      <div class="column is-7">
        <div class="field">
          <label for={attoId} class="label" title="End date and time for search range">Date To</label>
          <DateInput id={attoId} timePrecision="second" placeholder=" ---" min={minDate}
                     bind:disabled={attoNow} bind:valid={attoValid} bind:value={atto} />
        </div>
      </div>
      <div class="column is-5">
        <div class="field">
          <label for={attoNowId} class="label" title="use current date and time for Date To">or now</label>
          <div class="control checkbox ml-1 mt-2">
            <input id={attoNowId} type="checkbox" bind:checked={attoNow}>
          </div>
        </div>
      </div>
    </div>
  </div>
</div>
