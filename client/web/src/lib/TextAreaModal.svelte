<script>
  import { closeModal } from 'svelte-modals';

  export let isOpen;
  export let contentName;
  export let contentText;
  export let onApplyChanges;

  function applyChanges() {
    closeModal();
    onApplyChanges(contentText);
  }

  // TODO make textarea fill vertical space
</script>


<div class="modal" class:is-active={isOpen}>
  <div class="modal-background" on:click={closeModal}></div>
  <button class="modal-close is-large" aria-label="close" on:click={closeModal}></button>
  <div class="modal-content">
    <div class="box">
      <div class="field">
        <label for="text-editor" class="label">{contentName}</label>
        <div class="control">
          <textarea id="text-editor" class="textarea has-fixed-size" rows="18" bind:value={contentText}></textarea>
        </div>
      </div>
      <div class="field">
        <div class="control buttons">
          <button name="apply" class="button is-primary" on:click={applyChanges}>Apply</button>
          <button name="close" class="button" on:click={closeModal}>Close</button>
        </div>
      </div>
    </div>
  </div>
</div>


<style>
  .modal-content {
    width: 90%;
    height: 100%;
  }
</style>
