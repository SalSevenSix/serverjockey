<script>
  import { onMount, onDestroy, getContext, tick } from 'svelte';
  import { shortISODateTimeString, humanDuration } from 'common/util/util';
  import { eventsMap, mergeResults, extractResults, extractMeta,
           querySessions, queryChats } from 'common/activity/chat';
  import { ObjectUrls } from '$lib/util/browserutil';
  import { fetchJson } from '$lib/util/sjgmsapi';
  import SpinnerIcon from '$lib/widget/SpinnerIcon.svelte';

  const query = getContext('query');
  const objectUrls = new ObjectUrls();

  let processing = true;
  let results = null;
  let activity = null;

  $: query.blocker.notify('ChatActivityProcessing', processing);

  function queryActivity() {
    processing = true;
    const instance = query.criteria.instance().identity();
    const atrange = query.criteria.atrange();
    const player = query.criteria.search().text;
    const chatType = query.criteria.chat().type;
    const queries = [
      chatType === 'both' || chatType === 'session' ? fetchJson(querySessions(instance, atrange, player)) : null,
      chatType === 'both' || chatType === 'chat' ? fetchJson(queryChats(instance, atrange, player)) : null];
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
                  <i class={eventsMap[entry.event]}></i>&nbsp;&nbsp;{entry.event}
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
