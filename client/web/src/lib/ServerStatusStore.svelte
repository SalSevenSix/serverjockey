<script>
  import { onMount, onDestroy } from 'svelte';
  import { get } from 'svelte/store';
  import { generateId, sleep } from '$lib/util';
  import { notifyError } from '$lib/notifications';
  import { instance, serverStatus, SubscriptionHelper, newGetRequest } from '$lib/sjgmsapi';

  serverStatus.set({});
  let subs = new SubscriptionHelper();

  async function setServerStatus(data) {
    let id = generateId();
    data.id = id;
    serverStatus.set(data);
    if (!data.uptime) return;
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
        setServerStatus(json);
        subs.start($instance.url + '/server/subscribe', function(data) {
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
