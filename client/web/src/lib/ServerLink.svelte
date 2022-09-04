<script>
  import { goto } from '$app/navigation';
  import { onMount, onDestroy } from 'svelte';
  import { notifyError } from '$lib/notifications';
  import { baseurl, instance, serverStatus, SubscriptionHelper, newGetRequest } from '$lib/serverjockeyapi';
  import ServerStatus from '$lib/ServerStatus.svelte';
  import ServerControls from '$lib/ServerControls.svelte';
  import ServerLinkConfig from '$lib/ServerLinkConfig.svelte';

  instance.set({ url: baseurl + '/instances/serverlink' });  // used by ServerControls
  serverStatus.set({});  // used by ServerControls
  let subs = new SubscriptionHelper();

	onMount(function() {
    fetch(baseurl + '/instances/serverlink/server', newGetRequest())
      .then(function(response) {
        if (!response.ok) throw new Error('Status: ' + response.status);
        return response.json();
      })
      .then(function(json) {
        if (json.state === 'EXCEPTION') {
          goto('/setup');
        } else {
          serverStatus.set(json);
          subs.start(baseurl + '/instances/serverlink/server/subscribe', function(data) {
            serverStatus.set(data);
            return true;
          });
        }
      })
      .catch(function(error) { notifyError('Failed to load ServerLink Status.'); });
	});

	onDestroy(function() {
		subs.stop();
	});
</script>


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
