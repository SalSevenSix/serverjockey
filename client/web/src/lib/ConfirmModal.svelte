<script>
  import { closeModal } from 'svelte-modals';

  export let isOpen;
  export let message;
  export let onConfirm;

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
    <section id="confirmModalMessageSection" class="modal-card-body">
      {message}
    </section>
    <footer class="modal-card-foot">
      <button class="button is-success" on:click={confirm}>Confirm</button>
      <button class="button" on:click={closeModal}>Cancel</button>
    </footer>
  </div>
</div>


<style>
  #confirmModalMessageSection {
    white-space: pre;
  }
</style>
