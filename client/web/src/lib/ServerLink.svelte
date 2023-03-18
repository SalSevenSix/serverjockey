<script>
  import { onMount, onDestroy } from 'svelte';
  import { get } from 'svelte/store';
  import { sleep } from '$lib/util';
  import { notifyError } from '$lib/notifications';
  import { baseurl, instance, serverStatus, SubscriptionHelper, newGetRequest } from '$lib/serverjockeyapi';
  import Collapsible from '$lib/Collapsible.svelte';
  import ConsoleLog from '$lib/ConsoleLog.svelte';
  import ServerStatus from '$lib/ServerStatus.svelte';
  import ServerControls from '$lib/ServerControls.svelte';
  import ServerLinkConfig from '$lib/ServerLinkConfig.svelte';

  // used by ServerControls
  instance.set({ url: baseurl + '/instances/serverlink' });
  serverStatus.set({});
  let subs = new SubscriptionHelper();

  async function setServerStatus(data) {
    let id = Date.now().toString() + Math.random().toString().slice(1);
    data.id = id;
    serverStatus.set(data);
    if (!data.uptime) return;
    let looping = true;
    while (looping) {
      await sleep(20000);
      if (id === get(serverStatus).id) {
        data.uptime += 20000;
        serverStatus.set(data);
      } else {
        looping = false;
      }
    }
  }

  onMount(function() {
    fetch(baseurl + '/instances/serverlink/server', newGetRequest())
      .then(function(response) {
        if (!response.ok) throw new Error('Status: ' + response.status);
        return response.json();
      })
      .then(function(json) {
        setServerStatus(json);
        subs.start(baseurl + '/instances/serverlink/server/subscribe', function(data) {
          setServerStatus(data);
          return true;
        });
      })
      .catch(function(error) { notifyError('Failed to load ServerLink Status.'); });
  });

  onDestroy(function() {
    subs.stop();
  });
</script>


<div class="columns">
  <div class="column">
    <div class="columns">
      <div class="column">
        <h2 class="title is-5">ServerLink Controls</h2>
        <ServerControls />
        <ServerStatus />
      </div>
      <div class="column">
        <h2 class="title is-5">ServerLink Configuration</h2>
        <ServerLinkConfig />
      </div>
    </div>
    <Collapsible title="ServerLink Log">
      <ConsoleLog hasConsoleLogFile />
    </Collapsible>
  </div>
</div>
