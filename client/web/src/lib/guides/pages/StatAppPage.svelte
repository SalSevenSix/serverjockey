<script>
  import { surl } from '$lib/util/sjgmsapi';
  import CodeBlock from '$lib/widget/CodeBlock.svelte';
</script>


<div class="columns">
  <div class="column is-one-quarter content mb-0">
    <p class="has-text-centered pt-2">
      <i class="fa fa-tachograph-digital fa-8x theme-black-white"></i>
    </p>
  </div>
  <div class="column is-three-quarters content">
    <h2 class="title is-3 mt-2">The Status Dashboard</h2>
    <p>
      The Status Dashboard page is a static website you can optionally install to show instance status to the public.
      It includes current server state, players online, as well as player statistics for the last 30 days.
      An example of the page is shown below.
    </p><p>
      Prequisites are a user with root privilages (i.e.
      <span class="is-family-monospace notranslate">sudo</span>)
      and terminal access to the machine with familiarity using it. Setup also requires
      <a href={surl('/guides/nginx')}>Nginx</a>
      or similar to serve the static files.
    </p>
  </div>
</div>

<div class="content">
  <figure class="image max-1024">
    <img src={surl('/assets/guides/statapp/status_page.png')} alt="Status Dashboard Page" />
  </figure>
</div>

<div class="content">
  <p><span class="step-title"></span>
    First step is to use the the ServerJockey CLI to deploy that static website files to your chosen location.
    In the example below, the website is deployed to
    <span class="is-family-monospace white-space-nowrap notranslate">/var/www/statapp</span>
    using
    <span class="is-family-monospace notranslate">sudo</span>
    because the www directory is owned by root.
  </p>
  <CodeBlock>sudo serverjockey_cmd.pyz -c statapp-deploy:/var/www/statapp</CodeBlock>
</div>

<div class="content">
  <p><span class="step-title"></span>
    Configure your webserver to expose the files for this standalone static website. The
    <span class="has-text-weight-bold">Nginx</span>
    configuration shown below is
    <span class="is-italic">only provided as an example, and is not a complete configuration file.</span>
  </p><p>
    The example has the website available under
    <span class="is-family-monospace notranslate">/status</span>
    url path, serving files from
    <span class="is-family-monospace white-space-nowrap notranslate">/var/www/statapp</span>
    directory. Note that files under
    <span class="is-family-monospace white-space-nowrap notranslate">/var/www/statapp/data</span>
    should NOT be cached at all. These files will be periodically updated - more on that later.
  </p>
  <CodeBlock>
location /status &#123;
  alias /var/www/statapp/&#59;
&#125;

location /status/data/ &#123;
  alias /var/www/statapp/data/&#59;
  add_header Cache-Control &quot;no-store, no-cache, must-revalidate, proxy-revalidate, max-age=0&quot; always&#59;
  add_header Pragma &quot;no-cache&quot; always&#59;
  expires off&#59;
&#125;</CodeBlock>
</div>

<div class="content">
  <p><span class="step-title"></span>
    Now test the new website to make sure it&#39;s accessible. Open it in a browser and you should see
    a message that says &quot;no data found&quot;. This is expected, the data will be added next step.
  </p>
  <figure class="image max-800">
    <img src={surl('/assets/guides/statapp/no_data_message.png')} alt="No Data Message" />
  </figure>
</div>

<div class="content">
  <p><span class="step-title"></span>
    Data files for the Status Dashboard must be exported from ServerJockey using a CLI command.
    This snapshot of data keeps authentication to the ServerJockey API on the server.
    Also heavy access to the dashboard page will avoid overloading the API.
  </p><p>
    The command requires at least 3 comma delimited options. First the deployment path, same as used in the deployment
    command previously. Next is the timezone to use for statistics reporting. Then a list of instance names you want
    included on the page. Add additional instances with a comma as needed.
  </p><p>
    Example below is for timezone -4, and will report on the &quot;myserver&quot; instance. Once again
    <span class="is-family-monospace notranslate">sudo</span>
    is used because the target directory is owned by root.
    After you run the command with your own options, reload the Status Dashboard page to see results.
  </p>
  <CodeBlock>sudo serverjockey_cmd.pyz -c statapp-export:/var/www/statapp,-4,myserver</CodeBlock>
</div>

<div class="content">
  <p><span class="step-title"></span>
    To keep the data up-to-date, you will need to have the export command run periodically.
    One way to do this is with the cron service. Use
    <span class="is-family-monospace notranslate">sudo</span>
    again to edit the crontab for root, because the command needs to be run as root.
  </p>
  <CodeBlock>sudo crontab -e</CodeBlock>
  <p>
    The example crontab configuration line below will run the export command every 15 minutes.
    <span class="is-italic">Make sure you use your own command options.</span>
  </p>
  <CodeBlock>5,20,35,50 * * * * serverjockey_cmd.pyz -c statapp-export:/var/www/statapp,-4,myserver &gt; /dev/null 2&gt;&amp;1</CodeBlock>
</div>
