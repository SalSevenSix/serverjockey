<script>
  import { scrollto } from 'svelte-scrollto-next';
  import { surl } from '$lib/util/sjgmsapi';
  import GuideBooks from '$lib/svg/GuideBooks.svelte';
  import GeneralGuides from './GeneralGuides.svelte';
  import GameServerGuides from './GameServerGuides.svelte';
  import AdvancedGuides from './AdvancedGuides.svelte';
</script>


<div class="columns">
  <div class="column is-one-third content mb-0 pb-0">
    <figure class="image max-300"><GuideBooks /></figure>
  </div>
  <div class="column is-two-thirds content">
    <h2 class="title is-3 mt-2">Guides</h2>
    <p>
      If you are reading this, you have successfully installed and started
      <span class="has-text-weight-bold">ServerJockey</span>.
      Congratulations!
    </p>
    <p>
      The guides section will provide information on how to
      <a id="guidesPageDiscordBotSetup" href={surl('/guides/discord/setup')}>setup the Discord bot</a>.
      As well as help on how to setup, configure and start supported game servers, and more.
    </p>
    <ul>
      <li><a href="#generalguides" use:scrollto={'#generalguides'}>General Guides</a></li>
      <li><a href="#gameserverguides" use:scrollto={'#gameserverguides'}>Game Server Guides</a></li>
      <li><a href="#advancedguides" use:scrollto={'#advancedguides'}>Advanced Guides</a></li>
    </ul>
  </div>
</div>

<div class="content">
  <hr />
  <h3 id="generalguides" class="title is-4">General Guides</h3>
</div>
<GeneralGuides />

<div class="content">
  <hr />
  <h3 id="gameserverguides" class="title is-4">Game Server Guides</h3>
</div>
<GameServerGuides />

<div class="content">
  <hr />
  <h3 id="advancedguides" class="title is-4">Advanced Guides</h3>
</div>
<AdvancedGuides />
