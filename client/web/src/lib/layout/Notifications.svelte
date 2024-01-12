<script>
  import { notifications, removeNotification } from '$lib/util/notifications';

  function deleteMessage() {
    removeNotification(this.id);
  }
</script>


{#if $notifications.length > 0}
  <div id="notifications" class="section">
    <div class="container">
      {#each $notifications as notification, index}
        <div id={notification.id} role="button" tabindex="0" class="notification {notification.level}"
             on:click={deleteMessage} on:keypress={function() {}}>
          <i class="delete is-large mt-1 mr-1"></i>
          {#if notification.level === 'is-success'}<i class="fa fa-circle-check fa-lg"></i>{/if}
          {#if notification.level === 'is-warning'}<i class="fa fa-triangle-exclamation fa-lg"></i>{/if}
          {#if notification.level === 'is-danger'}<i class="fa fa-circle-minus fa-lg"></i>{/if}
          &nbsp;&nbsp;{notification.message}
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
    cursor: pointer;
  }
</style>
