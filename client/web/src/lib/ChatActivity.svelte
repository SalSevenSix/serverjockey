<script>
  import { onMount, onDestroy, getContext, tick } from 'svelte';
  import { shortISODateTimeString, humanDuration, ObjectUrls } from '$lib/util';
  import { newGetRequest } from '$lib/sjgmsapi';
  import { notifyError } from '$lib/notifications';
  import SpinnerIcon from '$lib/SpinnerIcon.svelte';

  const instance = getContext('instance');
  const query = getContext('query');
  const objectUrls = new ObjectUrls();

  let processing = true;
  let results = null;
  let activity = null;

  $: query.blocker.notify('ChatActivityProcessing', processing);

  async function queryChats(criteria) {
    processing = true;
    let atrange = criteria.atrange();
    let url = '/store/player/chat?instance=' + instance.identity();
    url += '&atfrom=' + atrange.atfrom + '&atto=' + atrange.atto;
    return await fetch(url, newGetRequest())
      .then(function(response) {
        if (!response.ok) throw new Error('Status: ' + response.status);
        return response.json();
      })
      .then(function(json) { return json; })
      .catch(function(error) { notifyError('Failed to query chat logs.'); })
      .finally(function() { processing = false; });
  }

  function extractActivity(data) {
    let last = { at: '', player: '' };
    let clazz = null;
    let chats = [];
    data.records.forEach(function(record) {
      let [at, player, text] = record;
      let atString = shortISODateTimeString(at);
      let atSection = atString.substring(0, 13);
      if (last.at != atSection) {
        chats.push({ clazz: 'row-hdr', ats: atString, at: atSection + 'h', player: null, text: null });
        last.at = atSection;
        clazz = null;
      }
      if (!clazz || last.player != player) {
        clazz = clazz === 'row-nrm' ? 'row-alt' : 'row-nrm';
      }
      last.player = player;
      chats.push({ clazz: clazz, ats: atString, at: atString.substring(14), player: player, text: text });
    });
    return { meta: { created: data.created, atfrom: data.criteria.atfrom, atto: data.criteria.atto,
             atrange: data.criteria.atto - data.criteria.atfrom }, results: chats };
  }

  query.execute = function() {
    queryChats(query.criteria).then(function(data) {
      results = data;
      activity = extractActivity(data);
    });
  }

  onMount(function() {
    tick().then(query.execute);
  });

  onDestroy(function() {
    objectUrls.cleanup();
  });
</script>


{#if processing}
  <div class="content ml-2 mb-4">
    <p><SpinnerIcon /> Loading Chat Log...</p>
  </div>
{:else if activity}
  <div class="content ml-2 mb-4">
    <p>
      <a href={'#'} on:click|preventDefault={function() { objectUrls.openObject(results); }}>
        results <i class="fa fa-up-right-from-square"></i></a>&nbsp;
      <span class="white-space-nowrap">from &nbsp;{shortISODateTimeString(activity.meta.atfrom)}&nbsp;</span>
      <span class="white-space-nowrap">to &nbsp;{shortISODateTimeString(activity.meta.atto)}&nbsp;</span>
      <span class="white-space-nowrap">({humanDuration(activity.meta.atrange)})</span>
    </p>
  </div>
{/if}

{#if activity}
  {#if activity.results.length === 0}
    <div class="content pb-4">
      <p><i class="fa fa-triangle-exclamation fa-lg ml-3 mr-1"></i> No chat activity found</p>
    </div>
  {:else}
    <div class="block chat-log-container mr-6"><div>
      <table class="table is-narrow is-log"><tbody>
        {#each activity.results as entry}
          <tr class={entry.clazz}>
            {#if entry.player}
              <td class="white-space-nowrap" title={entry.ats}>{entry.at}</td>
              <td>{entry.player}</td>
              <td>{entry.text}</td>
            {:else}
              <td class="white-space-nowrap has-text-weight-bold" colspan="2">{entry.at}</td>
              <td></td>
            {/if}
          </tr>
        {/each}
      </tbody><table>
    </div></div>
  {/if}
{/if}


<style>
  .chat-log-container {
    height: 360px;
    resize: vertical;
    overflow: auto;
  }

  .chat-log-container div {
    min-width: 400px;
    margin-right: auto;
  }
</style>
