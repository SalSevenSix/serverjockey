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
</script>


<div class="modal" class:is-active={isOpen}>
  <div class="modal-background" role="button" tabindex="0" on:click={closeModal} on:keypress={function() {}}></div>
  <div class="modal-content">
    <div class="box">
      <div class="field">
        <label for="textAreaModalEditor" class="label">{contentName}</label>
        <div class="control">
          <textarea id="textAreaModalEditor" class="textarea has-fixed-size is-family-monospace is-size-8"
                    bind:value={contentText}></textarea>
        </div>
      </div>
      <div class="field">
        <div class="control buttons">
          <button name="close" title="Close" class="button" on:click={closeModal}>
            <i class="fa fa-xmark fa-lg"></i>&nbsp;&nbsp;Close</button>
          <button name="save" title="Save" class="button is-primary" on:click={saveChanges}>
            <i class="fa fa-floppy-disk fa-lg"></i>&nbsp;&nbsp;Save</button>
        </div>
      </div>
    </div>
  </div>
</div>


<style>
  .modal-content {
    width: 95%;
    max-height: calc(100vh - 40px);
  }

  #textAreaModalEditor {
    height: 100%;
    min-height: calc(90vh - 8em);
  }
</style>
