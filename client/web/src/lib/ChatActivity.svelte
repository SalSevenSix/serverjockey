<script>
  import { onMount, onDestroy, getContext } from 'svelte';
  import { shortISODateTimeString, humanDuration, ObjectUrls } from '$lib/util';
  import { newGetRequest } from '$lib/sjgmsapi';
  import { notifyError } from '$lib/notifications';
  import SpinnerIcon from '$lib/SpinnerIcon.svelte';

  const instance = getContext('instance');
  const objectUrls = new ObjectUrls();

  let results = null;
  let activity = null;

  async function queryChats(criteria) {
    let url = '/store/player/chat?instance=' + criteria.instance;
    url += '&atfrom=' + criteria.atfrom + '&atto=' + criteria.atto;
    return await fetch(url, newGetRequest())
      .then(function(response) {
        if (!response.ok) throw new Error('Status: ' + response.status);
        return response.json();
      })
      .then(function(json) { return json; })
      .catch(function(error) { notifyError(errorMessage); });
  }

  function extractActivity(data) {
    let last = { at: '', player: ''};
    let clazz = 'row-alt';
    let chats = [];
    data.records.forEach(function(record) {
      let [at, player, text] = record;
      let atString = shortISODateTimeString(at);
      let atSection = atString.substring(0, 13);
      if (last.at != atSection) {
        chats.push({ clazz: 'row-hdr', ats: atString, at: atSection + 'h', player: null, text: null });
        last.at = atSection;
      }
      if (last.player != player) {
        clazz = clazz === 'row-nrm' ? 'row-alt' : 'row-nrm';
        last.player = player;
      }
      chats.push({ clazz: clazz, ats: atString, at: atString.substring(14), player: player, text: text });
    });
    return { meta: { created: data.created, atfrom: data.criteria.atfrom, atto: data.criteria.atto,
             atrange: data.criteria.atto - data.criteria.atfrom }, results: chats };
  }

  function queryActivity(criteria) {
    activity = null;
    queryChats(criteria).then(function(data) {
      results = data;
      activity = extractActivity(data);
    });
  }

  onMount(function() {
    let criteria = { instance: instance.identity() };
    criteria.atto = Date.now();
    criteria.atfrom = criteria.atto - 10800000;  // 3 hours
    queryActivity(criteria);
  });

  onDestroy(function() {
    objectUrls.cleanup();
  });
</script>


{#if activity}
  <div class="block">
    <div class="content ml-2 mb-4">
      <p>
        <a href={'#'} on:click|preventDefault={function() { objectUrls.openObjectAsText(results); }}>
          results <i class="fa fa-up-right-from-square"></i></a>&nbsp;
        <span class="white-space-nowrap">from &nbsp;{shortISODateTimeString(activity.meta.atfrom)}&nbsp;</span>
        <span class="white-space-nowrap">to &nbsp;{shortISODateTimeString(activity.meta.atto)}&nbsp;</span>
        <span class="white-space-nowrap">({humanDuration(activity.meta.atrange, 2)})</span>
      </p>
    </div>
    {#if activity.results.length > 0}
      <div class="block mr-6 chat-container"><table class="table is-narrow"><tbody>
        {#each activity.results as entry}
          {#if entry.player}
            <tr class={entry.clazz}>
              <td title={entry.ats}>{entry.at}</td>
              <td>{entry.player}</td>
              <td>{entry.text}</td>
            </tr>
          {:else}
            <tr class={entry.clazz}>
              <td class="has-text-weight-bold" colspan="3">{entry.at}</td>
            </tr>
          {/if}
        {/each}
      </tbody><table></div>
    {:else}
      <div class="content pb-4">
        <p><i class="fa fa-triangle-exclamation fa-lg ml-3 mr-1"></i> No chat activity found</p>
      </div>
    {/if}
  </div>
{:else}
  <div class="content">
    <p><SpinnerIcon /> Loading Chat Log...<br /><br /></p>
  </div>
{/if}


<style>
  .chat-container {
    height: 300px;
    overflow: scroll;
  }

  .chat-container .table {
    min-width: 400px;
  }

  .chat-container .table tr {
    background-color: white;
  }

  .chat-container .table tr td {
    color: black;
  }

  .chat-container .table tr td:last-child {
    border-left: 1px solid;
    border-color: #DBDBDB;
  }

  .row-hdr {
    opacity: 0.9;
  }

  .row-nrm {
    opacity: 0.8;
  }

  .row-alt {
    opacity: 0.7;
  }
</style>
