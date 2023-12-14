<script>
  import BackToTop from '$lib/BackToTop.svelte';
</script>


<div class="columns">
  <div class="column is-one-quarter content mb-0 pb-0">
    <figure class="image mr-0 max-300"><img src="/assets/brands/Virtualbox_logo.png" alt="Virtualbox logo" /></figure>
  </div>
  <div class="column is-three-quarters content">
    <h2 class="title is-3 mt-2">VirtualBox</h2>
    <p>
      <a href="https://www.virtualbox.org" target="_blank">VirtualBox <i class="fa fa-up-right-from-square"></i></a>
      is a free virtualization system for enterprise and personal use. It allows you to run a virtual machine on
      a real machine. ServerJockey is available as a VirtualBox Appliance (virtual machine).
      The appliance is running Ubuntu Server with ServerJockey pre-installed and ready to use.
    </p>
    <p>
      This guide provides some basic information on setting memory and processor allocations.
      For comprehensive information about VirtualBox, consult the
      <a href="https://www.virtualbox.org/manual/UserManual.html" target="_blank">
        online manual <i class="fa fa-up-right-from-square"></i></a>.
    </p>
  </div>
</div>

<div class="content">
  <h3 class="title is-4">Settings</h3>
  <p>
    You can configure how much of your real machine Memory and Processor the virtual machine is allowed to use.
    To do this click the <span class="has-text-weight-bold">Settings</span> cog button.
  </p>
  <figure class="image max-800">
    <img src="/assets/guides/virtualbox/main.png" alt="VirtualBox Settings" />
  </figure>
  <h3 class="title is-4">Memory Allocation</h3>
  <p>
    Select the <span class="has-text-weight-bold">System</span> section on the left panel,
    then the <span class="has-text-weight-bold">Motherboard</span> tab.
    The ServerJockey appliance has 10Gb of memory allocated. You can change this value as needed.
    It should less than how much free memory your real machine has, but enough to support the game server
    you are running with 2Gb spare.
  </p>
  <figure class="image max-800">
    <img src="/assets/guides/virtualbox/sysmem.png" alt="VirtualBox Memory" loading="lazy" />
  </figure>
  <h3 class="title is-4">Processor Allocation</h3>
  <p>
    On the <span class="has-text-weight-bold">Processor</span> tab you can adjust how much processor is allocated.
    You can specify a number of cores as well as an execution cap.
  </p>
  <figure class="image max-800">
    <img src="/assets/guides/virtualbox/syscpu.png" alt="VirtualBox Processor" loading="lazy" />
  </figure>
</div>

<BackToTop />
