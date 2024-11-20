<script>
  import { onMount, onDestroy, tick } from 'svelte';
  import { notifyError } from '$lib/util/notifications';
  import { RollingLog, toCamelCase } from '$lib/util/util';
  import { surl, SubscriptionHelper, newGetRequest } from '$lib/util/sjgmsapi';
  import ExtLink from '$lib/widget/ExtLink.svelte';

  const subs = new SubscriptionHelper();
  const logLines = new RollingLog();

  export let title = '';
  export let loadUrl;
  export let subscribeUrl;
  export let downloadUrl = null;
  export let heightSmall = '100px';
  export let heightBig = '420px';

  const idPrefix = 'consoleLog' + toCamelCase(title);

  let loading = true;
  let logBox;
  let logText = '';
  let logPlay = true;
  let logScroll = true;
  let logSmall = true;

  $: titlePlay = logPlay ? 'Pause' : 'Play';
  $: classPlay = logPlay ? 'fa-play' : 'fa-pause';
  $: titleScroll = logScroll ? 'Hold' : 'Scroll';
  $: classScroll = logScroll ? 'fa-unlock' : 'fa-lock';
  $: titleHeight = logSmall ? 'Expand' : 'Shrink';
  $: classHeight = logSmall ? 'fa-compress' : 'fa-expand';
  $: logHeight = logSmall ? heightSmall : heightBig;

  $: if (logScroll && logText && logBox) {
    scrollToBottom();
  }

  function scrollToBottom() {
    tick().then(function() {
      logBox.scroll({ top: logBox.scrollHeight });
    });
  }

  function toggleHeight() {
    logSmall = !logSmall;
    if (logScroll && logSmall) {
      scrollToBottom();
    }
  }

  function togglePlay() {
    logPlay = !logPlay;
    if (logPlay) {
      logText = logLines.toText();
    }
  }

  function toggleScroll() {
    logScroll = !logScroll;
  }

  function clearLog() {
    logText = logLines.reset().toText();
  }

  onMount(function() {
    fetch(surl(loadUrl), newGetRequest())
      .then(function(response) {
        if (!response.ok) throw new Error('Status: ' + response.status);
        return response.text();
      })
      .then(function(text) {
        logText = logLines.set(text).toText();
        subs.start(subscribeUrl, function(data) {
          logLines.append(data);
          if (logPlay) { logText = logLines.toText(); }
          return true;
        });
      })
      .catch(function(error) { notifyError('Failed to load Console Log.'); })
      .finally(function() { loading = false; });
  });

  onDestroy(function() {
    subs.stop();
  });
</script>


<div class="block pr-6">
  <div class="content mb-2">
    <span class="has-text-weight-bold">
      {#if downloadUrl}
        <ExtLink href={surl(downloadUrl)} title="Open" bigger>{title}&nbsp;</ExtLink>
      {:else}
        {title}
      {/if}
    </span>
    {#if loading}
      <span class="pl-2"><i class="fa fa-eraser fa-lg clear-button"></i></span>
      <span class="pl-2"><i class="fa {classPlay} fa-lg play-button"></i></span>
      <span class="pl-2"><i class="fa {classScroll} fa-lg scroll-button"></i></span>
      <span class="pl-2"><i class="fa {classHeight} fa-lg height-button"></i></span>
    {:else}
      <span class="pl-2"><a id="{idPrefix}Clear" href={'#'} title="Clear" on:click|preventDefault={clearLog}>
        <i class="fa fa-eraser fa-lg clear-button"></i>
      </a></span>
      <span class="pl-2"><a id="{idPrefix}Play" href={'#'} title={titlePlay} on:click|preventDefault={togglePlay}>
        <i class="fa {classPlay} fa-lg play-button"></i>
      </a></span>
      <span class="pl-2"><a id="{idPrefix}Scroll" href={'#'} title={titleScroll} on:click|preventDefault={toggleScroll}>
        <i class="fa {classScroll} fa-lg scroll-button"></i>
      </a></span>
      <span class="pl-2"><a id="{idPrefix}Height" href={'#'} title={titleHeight} on:click|preventDefault={toggleHeight}>
        <i class="fa {classHeight} fa-lg height-button"></i>
      </a></span>
    {/if}
  </div>
  <div class="block">
    <textarea id="{idPrefix}Text" class="textarea is-family-monospace is-size-7" style:height={logHeight}
              bind:this={logBox} disabled={loading} readonly>{logText}</textarea>
  </div>
</div>


<style>
  .clear-button {
    width: 1.2em;
  }

  .play-button {
    width: 0.8em;
  }

  .scroll-button {
    width: 0.9em;
  }

  .height-button {
    width: 1em;
  }
</style>
