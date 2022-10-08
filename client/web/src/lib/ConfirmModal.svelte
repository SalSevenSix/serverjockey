<script>
  import { closeModal } from 'svelte-modals';

  export let isOpen;
  export let onConfirm;
  export let message = 'Confirm action';
  export let confirmName = '';
  let enteredName = '';

	function confirm() {
    closeModal();
    onConfirm();
	}
</script>


<div class="modal" class:is-active={isOpen}>
  <div class="modal-background" on:click={closeModal}></div>
  <div class="modal-card">
    <header class="modal-card-head">
      <p class="modal-card-title">Confirm action</p>
      <button class="delete is-large" aria-label="close" on:click={closeModal}></button>
    </header>
    <section class="modal-card-body">
      <div id="confirmModalMessageContent" class="content">
        <p>{message}</p>
      </div>
      {#if confirmName}
        <div class="field">
          <label for="confirm-entered-name" class="label">Confirm Name</label>
          <div class="control">
            <input id="confirm-entered-name" class="input" type="text" bind:value={enteredName}>
          </div>
        </div>
      {/if}
    </section>
    <footer class="modal-card-foot">
      <button class="button is-success" disabled={confirmName != enteredName} on:click={confirm}>Confirm</button>
      <button class="button" on:click={closeModal}>Cancel</button>
    </footer>
  </div>
</div>


<style>
  #confirmModalMessageContent {
    white-space: pre;
  }
</style>
