<script>
  import { closeModal } from 'svelte-modals';

  export let isOpen;
  export let contentName;
  export let contentText;
  export let onSaveChanges;

  function saveChanges() {
    closeModal();
    onSaveChanges(contentText);
  }

  // TODO make textarea fill vertical space
</script>


<div class="modal" class:is-active={isOpen}>
  <div class="modal-background" on:click={closeModal} on:keypress={function() {}}></div>
  <button class="modal-close is-large" aria-label="close" on:click={closeModal}></button>
  <div class="modal-content">
    <div class="box">
      <div class="field">
        <label for="textAreaModalEditor" class="label">{contentName}</label>
        <div class="control">
          <textarea id="textAreaModalEditor" class="textarea has-fixed-size is-family-monospace is-size-8" rows="18"
                    bind:value={contentText}></textarea>
        </div>
      </div>
      <div class="field">
        <div class="control buttons">
          <button name="save" class="button is-primary" on:click={saveChanges}>Save</button>
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
