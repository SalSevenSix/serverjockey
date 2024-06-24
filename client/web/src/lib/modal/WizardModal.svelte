<script>
  // TODO unused

  import { closeModal } from 'svelte-modals';
  import { generateId } from '$lib/util/util';
  import InputRadio from '$lib/widget/InputRadio.svelte';
  import InputText from '$lib/widget/InputText.svelte';
  import InputTextArea from '$lib/widget/InputTextArea.svelte';

  const unique = generateId();

  export let isOpen;
  export let data;
  export let onSaveChanges;

  let section = Object.keys(data)[0];

  function uid(name) {
    return name + unique;
  }

  function saveChanges() {
    closeModal();
    onSaveChanges(data);
  }
</script>


<div class="modal" class:is-active={isOpen}>
  <div class="modal-background"></div>
  <div class="modal-card">
    <header class="modal-card-head">
      <p class="modal-card-title">WIZARD</p>
      <button class="delete is-large" aria-label="close" on:click={closeModal}></button>
    </header>
    <section class="modal-card-body">
      <div class="content">
        <p class="has-text-weight-bold">{section}</p>
        {#each Object.keys(data[section]) as item}
          {#if data[section][item].type === 'info'}
            <p>{data[section][item].value}</p>
          {:else if data[section][item].type === 'radio'}
            <p class="has-text-weight-bold mb-1">{data[section][item].name ? data[section][item].name : item}</p>
            <InputRadio name={uid(item)}
                        bind:group={data[section][item].value}
                        options={data[section][item].options} />
          {:else if data[section][item].type === 'string'}
            <InputText id={uid(item)}
                       name={data[section][item].name ? data[section][item].name : item}
                       bind:value={data[section][item].value} />
          {:else if data[section][item].type === 'text'}
            <InputTextArea id={uid(item)}
                           name={data[section][item].name ? data[section][item].name : item}
                           bind:value={data[section][item].value} />
          {/if}
        {/each}
      </div>
    </section>
    <footer class="modal-card-foot">
      <button title="Cancel" class="button" on:click={closeModal}>
        <i class="fa fa-rectangle-xmark fa-lg"></i>&nbsp;&nbsp;Cancel</button>
      <button title="Save" class="button is-success" on:click={saveChanges}>
        <i class="fa fa-square-check fa-lg"></i>&nbsp;&nbsp;Save</button>
    </footer>
  </div>
</div>
