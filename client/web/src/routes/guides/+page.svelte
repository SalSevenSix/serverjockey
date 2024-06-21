<script>
  import { surl } from '$lib/util/sjgmsapi';
  import GuideBooks from '$lib/svg/GuideBooks.svelte';
  import GeneralGuides from './GeneralGuides.svelte';
  import GameServerGuides from './GameServerGuides.svelte';
</script>


<div class="columns">
  <div class="column is-one-third content mb-0 pb-0">
    <figure class="image max-300"><GuideBooks /></figure>
  </div>
  <div class="column is-two-thirds content">
    <h2 class="title is-3 mt-2">Guides</h2>
    <p>
      If you are reading this, you have successfully installed and started
      <span class="has-text-weight-bold">ServerJockey</span>. Congratulations!
    </p>
    <p>
      The guides section will provide information on how to
      <a href={surl('/guides/discord/setup')}>setup the Discord bot</a>.
      As well as help on how to setup, configure and start supported game servers, and more.
    </p>
  </div>
</div>

<div class="content">
  <hr />
  <h3 class="title is-4">General Guides</h3>
</div>
<GeneralGuides />

<div class="content">
  <hr />
  <h3 class="title is-4">Game Server Guides</h3>
</div>
<GameServerGuides />
