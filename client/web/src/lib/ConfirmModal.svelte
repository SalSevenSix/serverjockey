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
  <div class="modal-background" on:click={closeModal} on:keypress={function() {}}></div>
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
          <label for="confirmModalName" class="label">Confirm Name</label>
          <div class="control">
            <input id="confirmModalName" class="input" type="text"
                   placeholder={confirmName} bind:value={enteredName}>
          </div>
        </div>
      {/if}
    </section>
    <footer class="modal-card-foot">
      <button class="button" on:click={closeModal}>
        <i class="fa fa-rectangle-xmark fa-lg"></i>&nbsp;&nbsp;Cancel</button>
      <button class="button is-success" disabled={confirmName != enteredName} on:click={confirm}>
        <i class="fa fa-square-check fa-lg"></i>&nbsp;&nbsp;Confirm</button>
    </footer>
  </div>
</div>


<style>
  #confirmModalMessageContent {
    white-space: pre;
  }
</style>
