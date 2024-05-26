<script>
  export let href;
  export let title = null;
  export let wrap = false;
  export let bigger = false;
  export let notranslate = false;
</script>


<a {href} {title} class:white-space-nowrap={!wrap} class:notranslate={notranslate}
   target="_blank"><slot />&nbsp;<i class="fa fa-up-right-from-square" class:fa-lg={bigger}></i></a>
