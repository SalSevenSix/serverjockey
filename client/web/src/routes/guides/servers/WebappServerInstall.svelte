<script>
  export let module;
</script>

<div class="content">
  <hr />
  <h3 class="title is-4">Server setup using the Webapp</h3>
</div>

<div class="content">
  <p><span class="step-title"></span>
    Go to the <a href="/servers" target="_blank">Instances <i class="fa fa-up-right-from-square"></i></a> page.
    If opened in a new tab, you will need to enter the login token again.
  </p>
  <figure class="image max-1024 is-bordered">
    <img src="/assets/setup/gg_goto_instances.png" alt="Go to instances page" />
  </figure>
</div>

<div class="content">
  <p><span class="step-title"></span>
    Find the <span class="has-text-weight-bold">New Instance</span> form on the Instances page.
    Select <span class="has-text-weight-bold">{module}</span> from the Module dropdown.
    Now give the instance a Name. The name must be lower case letters and numbers, no spaces or
    special characters except dashes and underscores.
    Click the <span class="has-text-weight-bold">Create</span> button to create the new instance.
  </p>
  <figure class="image max-400 is-bordered">
    <img src="/assets/setup/gg_new_instance.png" alt="Create a new instance" loading="lazy" />
  </figure>
</div>

<div class="content">
  <p><span class="step-title"></span>
    In the <span class="has-text-weight-bold">Instances</span> list on the same page you should find
    the new instance your created. View it now using the open folder button.
  </p>
  <figure class="image max-600 is-bordered">
    <img src="/assets/setup/gg_view_instance.png" alt="Go to new instance" loading="lazy" />
  </figure>
</div>

<div class="content">
  <p><span class="step-title"></span>
    Welcome to the control panel for your new instance! An instance is just a container for a game server.
    You can now install the actual server using this page.
    Scroll down and find the <span class="has-text-weight-bold">Deployment</span> section.
    Expand it using the black button on the right.
    Now click the <span class="has-text-weight-bold">Install Runtime</span> button.
  </p>
  <figure class="image max-1024 is-bordered">
    <img src="/assets/setup/gg_install_start.png" alt="Start install runtime" loading="lazy" />
  </figure>
  <p>
    Scroll back up to find the <span class="has-text-weight-bold">Console Log</span>.
    You can track the progress of the install process and see the end result in the log.
    Once completed successfully, you will be able to start the game server.
  </p>
  <figure class="image max-1024 is-bordered">
    <img src="/assets/setup/gg_install_log.png" alt="View install logging" loading="lazy" />
  </figure>
</div>
