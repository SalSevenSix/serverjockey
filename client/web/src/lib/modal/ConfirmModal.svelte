<script>
  import { closeModal } from 'svelte-modals';
  import { fNoop } from '$lib/util/util';
  import InputText from '$lib/widget/InputText.svelte';

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
  <div class="modal-background" on:click={closeModal} role="button" tabindex="0" on:keypress={fNoop}></div>
  <div class="modal-card">
    <header class="modal-card-head">
      <p class="modal-card-title">Confirm action</p>
      <button class="delete is-large" aria-label="close" on:click={closeModal}></button>
    </header>
    <section class="modal-card-body">
      <div class="content white-space-pre">
        <p>{message}</p>
      </div>
      {#if confirmName}
        <InputText id="confirmModalName" label="Confirm Name"
                   bind:value={enteredName} placeholder={confirmName}
                   title="Enter name to confirm action" autofocus notranslate />
      {/if}
    </section>
    <footer class="modal-card-foot">
      <button id="confirmModalCancel" title="Cancel" class="button" on:click={closeModal}>
        <i class="fa fa-rectangle-xmark fa-lg"></i>&nbsp;&nbsp;Cancel</button>
      <button id="confirmModalConfirm" title="Confirm" class="button is-success" on:click={confirm}
              disabled={confirmName != enteredName}>
        <i class="fa fa-square-check fa-lg"></i>&nbsp;&nbsp;Confirm</button>
    </footer>
  </div>
</div>
