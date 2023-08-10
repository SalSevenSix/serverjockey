<script>
  import { onMount, onDestroy, tick } from 'svelte';
  import { notifyError } from '$lib/notifications';
  import { RollingLog } from '$lib/util';
  import { SubscriptionHelper, newGetRequest } from '$lib/sjgmsapi';

  export let title = '';
  export let loadUrl;
  export let subscribeUrl;
  export let downloadUrl = null;
  export let heightSmall = '100px';
  export let heightBig = '420px';

  let subs = new SubscriptionHelper();
  let logLines = new RollingLog();
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
    tick().then(function() {
      logBox.scroll({ top: logBox.scrollHeight });
    });
  }

  function toggleHeight() {
    logSmall = !logSmall;
  }

  function togglePlay() {
    logPlay = !logPlay;
    if (logPlay) { logText = logLines.toText(); }
  }

  function toggleScroll() {
    logScroll = !logScroll;
  }

  function clearLog() {
    logText = logLines.reset().toText();
  }

  onMount(function() {
    fetch(loadUrl, newGetRequest())
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
      .catch(function(error) {
        notifyError('Failed to load Console Log.');
      });
  });

  onDestroy(function() {
    subs.stop();
  });
</script>


<div class="block pr-6">
  <div class="content mb-2">
    <span class="has-text-weight-bold">
      {#if downloadUrl}
        <a href={downloadUrl} title="Open" target="_blank">
          {title} &nbsp;<i class="fa fa-up-right-from-square fa-lg"></i></a>
      {:else}
        {title}
      {/if}
    </span>
    <span class="pl-2"><a href={'#'} title="Clear" on:click|preventDefault={clearLog}>
      <i class="fa fa-eraser fa-lg clear-button"></i>
    </a></span>
    <span class="pl-2"><a href={'#'} title={titlePlay} on:click|preventDefault={togglePlay}>
      <i class="fa {classPlay} fa-lg play-button"></i>
    </a></span>
    <span class="pl-2"><a href={'#'} title={titleScroll} on:click|preventDefault={toggleScroll}>
      <i class="fa {classScroll} fa-lg scroll-button"></i>
    </a></span>
    <span class="pl-2"><a href={'#'} title={titleHeight} on:click|preventDefault={toggleHeight}>
      <i class="fa {classHeight} fa-lg height-button"></i>
    </a></span>
  </div>
  <div class="block">
    <textarea bind:this={logBox} class="textarea is-family-monospace is-size-7"
              style:height={logHeight} readonly>{logText}</textarea>
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
