<script>
  import { surl } from '$lib/util/sjgmsapi';
  import ExtLink from '$lib/widget/ExtLink.svelte';
</script>


<div class="columns">
  <div class="column is-one-quarter">
    <ExtLink href={surl('/system/log')} title="Open" bigger>&nbsp;View Log&nbsp;</ExtLink>
  </div>
  <div class="column is-three-quarters">
    Open system log in a new tab.
  </div>
</div>
