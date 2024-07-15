<script>
  import { scrollto } from 'svelte-scrollto-next';
  import { surl } from '$lib/util/sjgmsapi';
  import TerminalCube from '$lib/svg/TerminalCube.svelte';
  import BackToTop from '$lib/widget/BackToTop.svelte';
  import CodeBlock from '$lib/widget/CodeBlock.svelte';
</script>


<div class="columns">
  <div class="column is-one-quarter content mb-0 pb-0">
    <figure class="image max-200"><TerminalCube /></figure>
  </div>
  <div class="column is-three-quarters content">
    <h2 class="title is-3 mt-2">Command Line Interface</h2>
    <p>
      This guide will show how to control servers and perform administrative tasks using the Command Line Interface
      (CLI). In order to use it, you must access a terminal to run the CLI executable.
    </p>
    <ul>
      <li><a href="#clishowhelp" use:scrollto={'#clishowhelp'}>Show Help</a></li>
      <li><a href="#clitasks" use:scrollto={'#clitasks'}>Tasks</a></li>
      <li><a href="#clicommands" use:scrollto={'#clicommands'}>Commands</a></li>
      <li><a href="#clibackup" use:scrollto={'#clibackup'}>Backup Example</a></li>
    </ul>
  </div>
</div>

<div class="content">
  <hr />
  <h3 id="clishowhelp" class="title is-4">Show Help</h3>
  <p>
    The CLI help text can be shown with the
    <span class="is-family-monospace notranslate">-h</span>
    option. There are two kinds of operations that can be performed.
    <span class="has-text-weight-bold">Tasks</span> and <span class="has-text-weight-bold">Commands</span>
    which are explained below.
  </p>
  <CodeBlock>serverjockey_cmd.pyz -h</CodeBlock>
  <figure class="image max-800">
    <img src={surl('/assets/guides/cli/cli_help.png')} alt="CLI help text" />
  </figure>

  <h3 id="clitasks" class="title is-4 pt-2">Tasks</h3>
  <p>
    Tasks are system admin operations that usually require root privilages (i.e.
    <span class="is-family-monospace notranslate">sudo</span>). Tasks are run using the
    <span class="is-family-monospace notranslate">-t</span>
    option. The example below will upgrade the ServerJockey system to the latest version.
  </p>
  <CodeBlock>sudo serverjockey_cmd.pyz -t upgrade</CodeBlock>

  <h3 id="clicommands" class="title is-4 pt-2">Commands</h3>
  <p>
    Commands are operations that interact with a running ServerJockey service to manage game servers.
    A list of Commands can be run using the
    <span class="is-family-monospace notranslate">-c</span>
    option. The example below will select the
    <span class="is-family-monospace notranslate">myserver</span>
    instance, then start the server.
  </p>
  <CodeBlock>serverjockey_cmd.pyz -c use:myserver server:start</CodeBlock>

  <h3 id="clibackup" class="title is-4 pt-2">Backup Example</h3>
  <p>
    The example below is a backup process for a Project Zomboid server. It can be run on a schedule using
    <span class="is-family-monospace notranslate">cron</span>.
    The process does the following...
  </p>
  <ol>
    <li>Select the instance called  <span class="is-family-monospace notranslate">myserver</span></li>
    <li>If the server is not running, then stop processing commands and exit</li>
    <li>Broadcast a 5 minute warning message to all players, then wait 4 minutes</li>
    <li>Broadcast a 1 minute warning message to all players, then wait 1 minute</li>
    <li>Stop the server then wait 10 seconds for that to happen</li>
    <li>Backup the game world save and delete all backups older than 168 hours</li>
    <li>Start up the server</li>
  </ol>
  <CodeBlock>
serverjockey_cmd.pyz -c \
  use:myserver exit-down \
  world-broadcast:"Server shutdown in 5 minutes. Please logout." sleep:240 \
  world-broadcast:"Server shutdown in 1 minute. Please logout." sleep:60 \
  server:stop sleep:10 \
  backup-world:168 \
  server:start</CodeBlock>
</div>

<BackToTop />
