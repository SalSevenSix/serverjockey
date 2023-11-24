<script>
  import { getContext, tick } from 'svelte';
	import { DateInput } from 'date-picker-svelte'  // https://date-picker-svelte.kasper.space/docs
  import { generateId } from '$lib/util';

  const query = getContext('query');
  const minDate = new Date(946684800000);  // 2000-01-01 00:00:00
  const [attoId, atfromId] = ['atto' + generateId(), 'atfrom' + generateId()];
  const atfromOptions = { '0': '<Date From>',
    '3600000': '1 hour', '10800000': '3 hours', '21600000': '6 hours', '43200000': '12 hours',
    '86400000': '24 hours', '604800000': '7 days', '1209600000': '14 days',
    '2592000000': '30 days', '5184000000': '60 days', '7776000000': '90 days'};

  export let defaultFromMillis = '2592000000';

  let atfrom = null;
  let atfromValid = false;
  let atto = null;
  let attoValid = false;
  let attoNow = true;
  let atfromMillis = defaultFromMillis;

  $: if (attoNow) { atto = null; } else { focusAttoField(); }
  $: hasAtfromMillis = atfromMillis != '0';
  $: if (hasAtfromMillis) { atfrom = null; } else { focusAtfromField(); }
  $: valid = validate(atfrom, atto, attoNow, atfromMillis);
  $: query.blocker.notify('QueryDateRangeInvalid', !valid);

  function focusAttoField() {
    tick().then(function() { document.getElementById(attoId).focus(); });
  }

  function focusAtfromField() {
    tick().then(function() { document.getElementById(atfromId).focus(); });
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
  <div class="column mr-6">
    <div class="field">
      <label for={atfromId} class="label" title="Begin date and time for search range">Date From</label>
      <DateInput id={atfromId} timePrecision="second" placeholder=" ---" min={minDate}
                 bind:disabled={hasAtfromMillis} bind:valid={atfromValid} bind:value={atfrom} />
    </div>
    <div class="field is-horizontal">
      <div class="field-label">
        <label for="queryDateRangeAtfromMillis" class="label white-space-nowrap"
               title="use preset range previous to Date To">or previous</label>
      </div>
      <div class="field-body">
        <div class="field is-narrow">
          <div class="control">
            <div class="select is-fullwidth is-small">
              <select class="select is-fullwidth" id="queryDateRangeAtfromMillis" bind:value={atfromMillis}>
                {#each Object.keys(atfromOptions) as key}
                  <option value={key}>{atfromOptions[key]}</option>
                {/each}
              </select>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
  <div class="column mr-6">
    <div class="field">
      <label for={attoId} class="label" title="End date and time for search range">Date To</label>
      <DateInput id={attoId} timePrecision="second" placeholder=" ---" min={minDate}
                 bind:disabled={attoNow} bind:valid={attoValid} bind:value={atto} />
    </div>
    <div class="field ml-3">
      <div class="control">
        <label class="checkbox has-text-weight-bold" title="use current date and time for Date To">
          <input type="checkbox" bind:checked={attoNow}>&nbsp; or now
        </label>
      </div>
    </div>
  </div>
</div>
