<script>
  import { fly, fade } from 'svelte/transition';
  import { notifications, removeNotification } from '$lib/util/notifications';

  const [baseMillis, incMillis, baseFly, incFly] = [200, 50, -120, 67];
  const icons = { 'is-success': 'fa-circle-check',
                  'is-warning': 'fa-triangle-exclamation',
                  'is-danger':  'fa-circle-minus' };

  function deleteMessage() {
    removeNotification(this.id);
  }
</script>


<div id="notifications" class="section" class:is-hidden={$notifications.length === 0}>
  <div class="container">
    {#each $notifications as notification, index}
      <div id={notification.id} class="notification {notification.level}"
           role="button" tabindex={index + 1} out:fade={{ duration: baseMillis }}
           in:fly={{ duration: (baseMillis + index * incMillis), y: (baseFly - index * incFly) }}
           on:click={deleteMessage} on:keypress={function() {}}>
        <i class="delete is-large mt-1 mr-1"></i>
        <i class="fa {icons[notification.level]} fa-lg"></i>&nbsp;&nbsp;
        {notification.message}
      </div>
    {/each}
  </div>
</div>


<style>
  #notifications {
    width: 100%;
    position: fixed;
    top: 0;
    z-index: 100;
  }

  .notification {
    margin: 0.2rem 1rem 0.2rem 1rem;
    cursor: pointer;
  }

  .notification:last-of-type {
    z-index: 110;
  }
</style>
