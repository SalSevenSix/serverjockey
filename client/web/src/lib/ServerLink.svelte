<script>
  import { onMount, onDestroy } from 'svelte';
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

  onMount(function() {
    fetch(baseurl + '/instances/serverlink/server', newGetRequest())
      .then(function(response) {
        if (!response.ok) throw new Error('Status: ' + response.status);
        return response.json();
      })
      .then(function(json) {
        serverStatus.set(json);
        subs.start(baseurl + '/instances/serverlink/server/subscribe', function(data) {
          serverStatus.set(data);
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
