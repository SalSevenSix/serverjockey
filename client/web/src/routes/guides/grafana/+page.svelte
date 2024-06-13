<script>
  import { scrollto } from 'svelte-scrollto-next';
  import { surl } from '$lib/util/sjgmsapi';
  import GrafanaIcon from '$lib/svg/GrafanaIcon.svelte';
  import BackToTop from '$lib/widget/BackToTop.svelte';
  import ExtLink from '$lib/widget/ExtLink.svelte';
  import CodeBlock from '$lib/widget/CodeBlock.svelte';
</script>


<div class="columns">
  <div class="column is-one-quarter content mb-0 pb-0">
    <figure class="image mt-2 max-200"><GrafanaIcon /></figure>
  </div>
  <div class="column is-three-quarters content">
    <h2 class="title is-3 mt-2">Something Grafana</h2>
    <p>
      TODO
    </p>
  </div>
</div>

<BackToTop />
