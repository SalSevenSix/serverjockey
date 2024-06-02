<script>
  import { onMount, onDestroy, tick, setContext } from 'svelte';
  import { writable } from 'svelte/store';
  import { notifyError } from '$lib/util/notifications';
  import { surl, newGetRequest, SubscriptionHelper } from '$lib/util/sjgmsapi';

  const subs = new SubscriptionHelper();

  export let identity = null;

  let triggering = false;

  function getInstanceModule() {
    const parts = window.location.pathname.split('/');
    let result = '';
    while (parts.length > 0 && !result) { result = parts.pop(); }
    return result;
  }

  function getInstanceIdentity() {
    if (identity) return identity;
    return new URLSearchParams(window.location.search).get('i');
  }

  function getInstanceUrl(path = null) {
    let url = window.location.protocol + '//';
    url += window.location.hostname;
    if (window.location.port) {
      url += ':' + window.location.port;
    }
    url += surl('/instances/' + getInstanceIdentity());
    return path ? url + path : url;
  }

  const instance = { module: getInstanceModule, identity: getInstanceIdentity, url: getInstanceUrl };
  setContext('instance', instance);

  const serverStatus = writable({});
  setContext('serverStatus', serverStatus);

  const eventDown = writable(false);
  setContext('eventDown', eventDown);

  const eventStarted = writable(false);
  setContext('eventStarted', eventStarted);

  const eventEndMaint = writable(false);
  setContext('eventEndMaint', eventEndMaint);

  let lastRunning = null;
  $: serverRunningChange($serverStatus.running); function serverRunningChange(serverRunning) {
    if (triggering && lastRunning != serverRunning && serverRunning === false) {
      eventDown.set(true);
      tick().then(function() { eventDown.set(false); });
    }
    lastRunning = serverRunning;
  }

  let lastState = null;
  $: serverStateChange($serverStatus.state); function serverStateChange(serverState) {
    if (triggering && lastState != serverState && serverState === 'STARTED') {
      eventStarted.set(true);
      tick().then(function() { eventStarted.set(false); });
    }
    if (triggering && lastState != serverState && lastState === 'MAINTENANCE') {
      eventEndMaint.set(true);
      tick().then(function() { eventEndMaint.set(false); });
    }
    lastState = serverState;
  }

  onMount(function() {
    fetch(instance.url('/server'), newGetRequest())
      .then(function(response) {
        if (!response.ok) throw new Error('Status: ' + response.status);
        return response.json();
      })
      .then(function(json) {
        lastRunning = json.running;
        lastState = json.state;
        serverStatus.set(json);
        subs.start(instance.url('/server/subscribe'), function(data) {
          triggering = true;
          serverStatus.set(data);
          return true;
        });
      })
      .catch(function(error) {
        notifyError('Failed to load Server Status.');
      });
  });

  onDestroy(function() {
    subs.stop();
  });
</script>


<slot />
