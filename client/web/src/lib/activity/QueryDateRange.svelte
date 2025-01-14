<script>
  import { getContext, tick } from 'svelte';
  import { DateInput } from 'date-picker-svelte';  // https://date-picker-svelte.kasper.space/docs

  const query = getContext('query');
  const minDate = new Date(946684800000);  // 2000-01-01 00:00:00
  const attoId = 'queryDateRange' + query.contextId + 'Itodt';
  const attoPresetId = 'queryDateRange' + query.contextId + 'Stopreset';
  const atfromId = 'queryDateRange' + query.contextId + 'Ifromdt';
  const atfromMillisId = 'queryDateRange' + query.contextId + 'Sfromms';
  const attoOptions = [' ---', 'Now', 'Last Hour', 'Last Day', 'Last Month', 'This Month'];
  const atfromOptions = { '0': ' ---',
    '3600000': '1 hour', '10800000': '3 hours', '21600000': '6 hours', '43200000': '12 hours',
    '86400000': '24 hours', '604800000': '7 days', '1209600000': '14 days',
    '2592000000': '30 days', '5184000000': '60 days', '7776000000': '90 days' };

  export let headless = false;
  export let defaultFromMillis = '2592000000';

  let updating = false;
  let [atfrom, atfromValid, atfromMillis] = [null, false, defaultFromMillis];
  let [atto, attoValid, attoPreset] = [null, false, attoOptions[1]];

  $: hasAttoPreset = attoPreset != attoOptions[0];
  $: if (hasAttoPreset) { atto = null; } else { focusElement(attoId); }
  $: if (attoOptions.indexOf(attoPreset) > 3) { onAttoPresetMonth(); }
  $: hasAtfromMillis = atfromMillis != '0';
  $: if (hasAtfromMillis) { atfrom = null; } else { focusElement(atfromId); }
  $: valid = validate(atfrom, atto, attoPreset, atfromMillis);
  $: query.blocker.notify('QueryDateRangeInvalid', !valid);

  function onAttoPresetMonth() {
    tick().then(function() {
      let hadFromMillis = false;
      if (hasAtfromMillis) {
        hadFromMillis = true;
        atfromMillis = '0';
      }
      const now = new Date();
      const month = attoPreset == attoOptions[4] ? now.getMonth() - 1 : now.getMonth();
      atfrom = new Date(now.getFullYear(), month);
      if (!hadFromMillis) { focusElement(atfromId); }
    });
  }

  function focusElement(elementId) {
    if (updating) return;
    tick().then(function() { document.getElementById(elementId).focus(); });
  }

  function validate() {
    if (atfrom && !atfromValid) return false;
    if (atto && !attoValid) return false;
    const resolvable = (atto || hasAttoPreset) && (atfrom || hasAtfromMillis);
    if (!resolvable) return false;
    const millis = resolveRange();
    if (millis.atfrom >= millis.atto) return false;
    return true;
  }

  function attoPresetToMillis(selected) {
    let dt = new Date();
    if (selected == attoOptions[2]) {
      dt = new Date(dt.getFullYear(), dt.getMonth(), dt.getDate(), dt.getHours());
    } else if (selected == attoOptions[3]) {
      dt = new Date(dt.getFullYear(), dt.getMonth(), dt.getDate());
    } else if (selected == attoOptions[4]) {
      dt = new Date(dt.getFullYear(), dt.getMonth());
    } else if (selected == attoOptions[5]) {
      dt = new Date(dt.getFullYear(), dt.getMonth() + 1);
    }
    return dt.getTime();
  }

  function resolveRange() {
    const millis = { atfrom: null, atto: null };
    if (atto) { millis.atto = Math.trunc(atto.getTime() / 1000) * 1000; }
    if (hasAttoPreset) { millis.atto = attoPresetToMillis(attoPreset); }
    if (atfrom) { millis.atfrom = Math.trunc(atfrom.getTime() / 1000) * 1000; }
    if (hasAtfromMillis) { millis.atfrom = millis.atto - parseInt(atfromMillis, 10); }
    return millis;
  }

  query.callups.setRange = function(from, to) {
    updating = true;
    [attoPreset, atfromMillis] = [attoOptions[0], '0'];
    [atto, atfrom] = [to, from];
    tick().then(function() { updating = false; });
  };

  query.criteria.atrange = function() {
    const millis = resolveRange();
    return { atfrom: millis.atfrom.toString(), atto: millis.atto.toString() };
  };
</script>


{#if !headless}
  <div class="columns">
    <div class="column">
      <div class="columns is-gapless">
        <div class="column is-7">
          <div class="field">
            <label for={atfromId} class="label" title="Begin date and time for search range">Date From</label>
            <div class="notranslate">
              <DateInput id={atfromId} timePrecision="second" placeholder=" ---" min={minDate}
                         bind:disabled={hasAtfromMillis} bind:valid={atfromValid} bind:value={atfrom} />
            </div>
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
      <div class="columns is-gapless">
        <div class="column is-7">
          <div class="field">
            <label for={attoId} class="label" title="End date and time for search range">Date To</label>
            <div class="notranslate">
              <DateInput id={attoId} timePrecision="second" placeholder=" ---" min={minDate}
                         bind:disabled={hasAttoPreset} bind:valid={attoValid} bind:value={atto} />
            </div>
          </div>
        </div>
        <div class="column is-5">
          <div class="field">
            <label for={attoPresetId} class="label" title="use preset date and time">or preset</label>
            <div class="control select">
              <select id={attoPresetId} bind:value={attoPreset}>
                {#each attoOptions as option}
                  <option>{option}</option>
                {/each}
              </select>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
{/if}
