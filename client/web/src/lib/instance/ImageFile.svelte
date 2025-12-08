<script>
  import { getContext } from 'svelte';
  import FileUpload from '$lib/instance/FileUpload.svelte';

  const instance = getContext('instance');

  export let path;
  export let idPrefix = 'fileImage';

  function freshPath() {
    return path + '?' + Date.now().toString();
  }

  let imagePath = freshPath();
  function onCompleted() {
    imagePath = freshPath();
  }
</script>


<div class="content"><figure class="image maxh is-bordered">
  <img src={instance.url(imagePath)} alt="No Logo Set" />
</figure></div>

<FileUpload idPrefix={idPrefix} rootPath={path} filenameHelp={null} onCompleted={onCompleted} nospinner />


<style>
  figure.maxh img {
    width: auto;
    max-height: 240px;
  }
</style>
