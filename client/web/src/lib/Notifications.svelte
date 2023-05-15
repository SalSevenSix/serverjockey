<script>
  import { notifications, removeNotification } from '$lib/notifications';

  function deleteMessage() {
    removeNotification(this.name);
  }
</script>


{#if $notifications.length > 0}
  <div id="notifications" class="section">
    <div class="container">
      {#each $notifications as notification, index}
        <div class="notification {notification.level}">
          <button name="{notification.id}" class="delete is-large" on:click={deleteMessage}></button>
          {notification.message}
        </div>
      {/each}
    </div>
  </div>
{/if}


<style>
  #notifications {
    width: 100%;
    position: fixed;
    top: 0;
    z-index: 100;
  }

  .notification {
    margin: 0.2rem 1rem 0.2rem 1rem;
  }
</style>
