<script>
  import { closeModal } from 'svelte-modals';

  export let isOpen;
  export let contentName;
  export let contentText;
  export let onSave;

  function save() {
    onSave(contentText);
  }

  function saveAndClose() {
    closeModal();
    onSave(contentText);
  }
</script>


<div class="modal" class:is-active={isOpen}>
  <div class="modal-background"></div>
  <div class="modal-content">
    <div class="box">
      <div class="field">
        <label for="textAreaModalText" class="label">{contentName}</label>
        <div class="control">
          <textarea id="textAreaModalText" class="textarea has-fixed-size is-family-monospace full-height"
                    spellcheck="false" bind:value={contentText}></textarea>
        </div>
      </div>
      <div class="field">
        <div class="control buttons">
          <button id="textAreaModalClose" title="Close" class="button" on:click={closeModal}>
            <i class="fa fa-xmark fa-lg"></i>&nbsp;&nbsp;Close</button>
          <button id="textAreaModalSave" title="Save" class="button is-primary is-hidden-mobile" on:click={save}>
            <i class="fa fa-floppy-disk fa-lg"></i>&nbsp;&nbsp;Save</button>
          <button id="textAreaModalSaveClose" title="Save and Close" class="button is-primary" on:click={saveAndClose}>
            <i class="fa fa-floppy-disk fa-lg"></i>&nbsp;&nbsp;Save&nbsp;&amp;&nbsp;Close</button>
        </div>
      </div>
    </div>
  </div>
</div>


<style>
  .modal-content {
    min-width: 95%;
    max-height: 100vh;
    max-height: 100dvh;
  }

  .full-height {
    min-height: calc(90vh - 8em);
    min-height: calc(90dvh - 8em);
  }
</style>
