<script>
  import { onMount, onDestroy, getContext, tick } from 'svelte';
  import { shortISODateTimeString, humanDuration, ObjectUrls } from '$lib/util/util';
  import { newGetRequest } from '$lib/util/sjgmsapi';
  import { notifyError } from '$lib/util/notifications';
  import { queryFetch } from '$lib/activity/common';
  import SpinnerIcon from '$lib/widget/SpinnerIcon.svelte';

  const query = getContext('query');
  const objectUrls = new ObjectUrls();

  let processing = true;
  let results = null;
  let activity = null;

  $: query.blocker.notify('ChatActivityProcessing', processing);

  async function querySessions(instance, atrange, player) {
    let url = '/store/player/event?instance=' + instance;
    url += '&atfrom=' + atrange.atfrom + '&atto=' + atrange.atto;
    if (player) { url += '&player=' + player; }
    url += '&verbose';
    return await queryFetch(url, 'Failed to query player events.');
  }

  async function queryChats(instance, atrange, player) {
    let url = '/store/player/chat?instance=' + instance;
    url += '&atfrom=' + atrange.atfrom + '&atto=' + atrange.atto;
    if (player) { url += '&player=' + player; }
    return await queryFetch(url, 'Failed to query chat logs.');
  }

  function mergeResults(data) {
    const result = [];
    if (data.chat) {
      data.chat.records.forEach(function(record) {
        result.push({ at: record[0], player: record[1], text: record[2] });
      });
    }
    if (data.session) {
      data.session.records.forEach(function(record) {
        result.push({ at: record[0], player: record[2], steamid: record[4], event: record[3] });
      });
    }
    result.sort(function(left, right) {
      return left.at - right.at;
    });
    return result;
  }

  function extractResults(data) {
    const last = { at: '', player: '' };
    const result = [];
    let clazz = null;
    data.forEach(function(item) {
      const atString = shortISODateTimeString(item.at);
      const atSection = atString.substring(0, 13);
      if (last.at != atSection) {
        result.push({ clazz: 'row-hdr', ats: atString, at: atSection + 'h' });
        last.at = atSection;
        clazz = null;
      }
      if (!clazz || last.player != item.player) {
        clazz = clazz === 'row-nrm' ? 'row-alt' : 'row-nrm';
      }
      last.player = item.player;
      const entry = { clazz: clazz, ats: atString, at: atString.substring(14), player: item.player };
      if (item.event) {
        entry.event = item.event;
        entry.text = item.steamid;
      } else {
        entry.text = item.text;
      }
      result.push(entry);
    });
    return result;
  }

  function extractMeta(data) {
    return { created: data.created, atfrom: data.criteria.atfrom, atto: data.criteria.atto,
             atrange: data.criteria.atto - data.criteria.atfrom };
  }

  function queryActivity() {
    processing = true;
    const instance = query.criteria.instance().identity();
    const atrange = query.criteria.atrange();
    const player = query.criteria.search().text;
    const chatType = query.criteria.chat().type;
    const queries = [null, null];
    if (chatType === 'both' || chatType === 'session') { queries[0] = querySessions(instance, atrange, player); }
    if (chatType === 'both' || chatType === 'chat') { queries[1] = queryChats(instance, atrange, player); }
    Promise.all(queries)
      .then(function(data) {
        results = {};
        [results.session, results.chat] = data;
        activity = { meta: extractMeta(results.chat ? results.chat : results.session),
                     results: extractResults(mergeResults(results)) };
      })
      .finally(function() { processing = false; });
  }

  query.onExecute('ChatActivity', queryActivity);

  onMount(function() {
    tick().then(queryActivity);
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
        results&nbsp;<i class="fa fa-up-right-from-square"></i></a>&nbsp;
      <span class="white-space-nowrap">from &nbsp;{shortISODateTimeString(activity.meta.atfrom)}&nbsp;</span>
      <span class="white-space-nowrap">to &nbsp;{shortISODateTimeString(activity.meta.atto)}&nbsp;</span>
      <span class="white-space-nowrap notranslate">({humanDuration(activity.meta.atrange)})</span>
    </p>
  </div>
{/if}

{#if activity}
  {#if activity.results.length === 0}
    <div id="chatActivity{query.contextId}None" class="content pb-4">
      <p><i class="fa fa-triangle-exclamation fa-lg ml-3 mr-1"></i> No chat activity found</p>
    </div>
  {:else}
    <div class="block chat-log-container mr-6"><div>
      <table class="table is-narrow is-log"><tbody id="chatActivity{query.contextId}List">
        {#each activity.results as entry}
          <tr class={entry.clazz}>
            {#if entry.player}
              <td class="white-space-nowrap notranslate" title={entry.ats}>{entry.at}</td>
              <td class="notranslate">{entry.player}</td>
              {#if entry.event}
                <td>
                  <span class="white-space-nowrap">
                    {#if entry.event === 'LOGIN'}
                      <i class="fa fa-right-to-bracket"></i>&nbsp; LOGIN
                    {:else}
                      <i class="fa fa-right-to-bracket rotate-180"></i>&nbsp; LOGOUT
                    {/if}
                  </span>
                  {#if entry.text}&nbsp;({entry.text}){/if}
                </td>
              {:else}
                <td class="notranslate">{entry.text}</td>
              {/if}
            {:else}
              <td class="white-space-nowrap has-text-weight-bold notranslate" colspan="2">{entry.at}</td>
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
  }
</style>
