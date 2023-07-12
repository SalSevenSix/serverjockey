<script>
  import { onMount, onDestroy, tick } from 'svelte';
  import { get } from 'svelte/store';
  import { generateId, sleep } from '$lib/util';
  import { notifyError } from '$lib/notifications';
  import { SubscriptionHelper, newGetRequest } from '$lib/sjgmsapi';
  import { instance, serverStatus, eventDown, eventStarted, eventEndMaint } from '$lib/instancestores';

  let subs = new SubscriptionHelper();
  let triggering = false;

  serverStatus.set({});
  eventDown.set(false);
  eventStarted.set(false);
  eventEndMaint.set(false);

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

  async function setServerStatus(data) {
    let id = generateId();
    data.id = id;
    serverStatus.set(data);
    if (!data.uptime) return;
    // TODO try a better way to update uptime, perhaps use a seperate store and use real clock time
    let looping = true;
    while (looping) {
      await sleep(10000);
      if (id === get(serverStatus).id) {
        data.uptime += 10000;
        serverStatus.set(data);
      } else {
        looping = false;
      }
    }
  }

  onMount(function() {
    if (!$instance.url) return;
    fetch($instance.url + '/server', newGetRequest())
      .then(function(response) {
        if (!response.ok) throw new Error('Status: ' + response.status);
        return response.json();
      })
      .then(function(json) {
        lastRunning = json.running;
        lastState = json.state;
        setServerStatus(json);
        subs.start($instance.url + '/server/subscribe', function(data) {
          triggering = true;
          setServerStatus(data);
          return true;
        });
      })
      .catch(function(error) { notifyError('Failed to load Server Status.'); });
  });

  onDestroy(function() {
    subs.stop();
  });
</script>


<slot />
