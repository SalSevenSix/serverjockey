<script>
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
    <h2 class="title is-3 mt-2">Installing Grafana</h2>
    <p>
      <ExtLink href="https://grafana.com" notranslate>Grafana</ExtLink>
      is a popular observability platform often paired with Prometheus to provide comprehensive graphing
      and alerts. This guide will show how to install the open source (OSS) version of Grafana
      and integrate it with Prometheus. Prequisites are a user with root privilages (i.e. sudo)
      and terminal access to the machine with familiarity using it.
    </p>
  </div>
</div>

<div class="content">
  <hr />
  <p><span class="step-title"></span>
    Before beginning the install process, check the
    <ExtLink href="https://grafana.com/grafana/download?edition=oss&pg=get&platform=linux&plcmt=selfmanaged-box1-cta1">downloads page</ExtLink>
    to confirm the latest Grafana OSS version to install. Also see the official Grafana OSS
    <ExtLink href="https://grafana.com/docs/grafana/latest/getting-started/build-first-dashboard/?pg=oss-graf&plcmt=resources">setup guide</ExtLink>
    for general information. If you are planning to host the Grafana web console behind Nginx, see the
    <ExtLink href="https://grafana.com/tutorials/run-grafana-behind-a-proxy/">reverse proxy guide</ExtLink>
    for details. The commands in this guide are for Grafana version
    <span class="is-family-monospace notranslate">11.0.0</span>
  </p>

  <p><span class="step-title"></span>
    First install some dependencies required by Grafana.
  </p>
  <CodeBlock>sudo apt-get install -y adduser libfontconfig1 musl</CodeBlock>

  <p><span class="step-title"></span>
    Then download the DEB package and install it with the package manager.
  </p>
  <CodeBlock>wget https://dl.grafana.com/oss/release/grafana_11.0.0_amd64.deb</CodeBlock>
  <CodeBlock>sudo dpkg -i grafana_11.0.0_amd64.deb</CodeBlock>

  <p><span class="step-title"></span>
    The package will install Grafana as a systemd service.
    However it does not enable or start the service.
    Use the commands below to finish the service setup.
  </p>
  <CodeBlock>sudo systemctl daemon-reload</CodeBlock>
  <CodeBlock>sudo systemctl enable grafana-server</CodeBlock>
  <CodeBlock>sudo systemctl start grafana-server</CodeBlock>

  <p><span class="has-text-weight-bold">Hint:</span>
    At any time you can check the status of the Grafana service to see if it&#39;s running.
  </p>
  <CodeBlock>sudo systemctl status grafana-server</CodeBlock>
  <figure class="image max-1024">
    <img src={surl('/assets/guides/grafana/service_status.png')} alt="Grafana Service Status" />
  </figure>

  <p><span class="step-title"></span>
    Now open the Grafana console in a browser using the machine IP or hostname.
    By default Grafana uses http listening on port
    <span class="is-family-monospace">3000</span>.
    Login with username
    <span class="is-family-monospace notranslate">admin</span>
    and password
    <span class="is-family-monospace notranslate">admin</span>
    too. Please change the default password for the admin user immediately after login.
  </p>
  <figure class="image max-1024">
    <img src={surl('/assets/guides/grafana/01_first_login.jpg')} alt="First Login" loading="lazy" />
  </figure>

  <p><span class="step-title"></span>
    To integrate Prometheus, it needs to be connected as a data source. Find the menu then go to the
    <span class="has-text-weight-bold">Connections &gt; Add new connection</span>
    page.
  </p>
  <figure class="image max-1024">
    <img src={surl('/assets/guides/grafana/02_menu_new_connection.png')} alt="Menu New Connection" loading="lazy" />
  </figure>

  <p><span class="step-title"></span>
    Find and click the Prometheus data source.
  </p>
  <figure class="image max-1024">
    <img src={surl('/assets/guides/grafana/03_select_prometheus.png')} alt="Select Prometheus" loading="lazy" />
  </figure>

  <p><span class="step-title"></span>
    On the Prometheus data source page, click the
    <span class="has-text-weight-bold">Add new data source</span>
    button.
  </p>
  <figure class="image max-1024">
    <img src={surl('/assets/guides/grafana/04_view_prometheus.png')} alt="View Prometheus" loading="lazy" />
  </figure>

  <p><span class="step-title"></span>
    Now configure the new Prometheus data source connection. Keep the default
    <span class="has-text-weight-bold">Name</span>
    and
    <span class="has-text-weight-bold">Default</span>
    setting.
  </p>
  <figure class="image max-1024">
    <img src={surl('/assets/guides/grafana/05_config_page.png')} alt="Config Page" loading="lazy" />
  </figure>

  <p><span class="step-title"></span>
    Scroll down to the
    <span class="has-text-weight-bold">Connection</span>
    section and set the URL as shown below.
  </p>
  <CodeBlock>http://localhost:9090</CodeBlock>
  <figure class="image max-1024">
    <img src={surl('/assets/guides/grafana/06_config_url.png')} alt="Config URL" loading="lazy" />
  </figure>

  <p><span class="step-title"></span>
    Scroll down further to the
    <span class="has-text-weight-bold">Performance</span>
    section. Set the
    <span class="has-text-weight-bold">Prometheus type</span>
    to
    <span class="is-family-monospace notranslate">Prometheus</span>
    and the
    <span class="has-text-weight-bold">Prometheus version</span>
    to the appropriate value for the version installed.
  </p>
  <figure class="image max-1024">
    <img src={surl('/assets/guides/grafana/07_config_performance.png')} alt="Config Performance" loading="lazy" />
  </figure>

  <p><span class="step-title"></span>
    Click
    <span class="has-text-weight-bold">Save &amp; test</span>
    to save the connection configuration. Expect a success dialog as shown below.
  </p>
  <figure class="image max-1024">
    <img src={surl('/assets/guides/grafana/08_config_save.png')} alt="Config Save" loading="lazy" />
  </figure>

  <p><span class="step-title"></span>
    With Prometheus now connected, machine metrics can be reported by importing a pre-made Dashboard.
    In the menu go to the
    <span class="has-text-weight-bold">Dashboard</span>
    page. Then click the
    <span class="has-text-weight-bold">Import</span>
    option from the
    <span class="has-text-weight-bold">New</span>
    dropdown-button.
  </p>
  <figure class="image max-1024">
    <img src={surl('/assets/guides/grafana/09_import_dashboard.png')} alt="Import Dashboard" loading="lazy" />
  </figure>

  <p><span class="step-title"></span>
    Now import a popular machine metrics dashboard using the URL as shown below. Click the
    <span class="has-text-weight-bold">Load</span>
    button to begin importing the dashboard. Feel free to explore the
    <ExtLink href="https://grafana.com/grafana/dashboards/">Grafana dashboards page</ExtLink>
    to import any dashboard you want.
  </p>
  <CodeBlock>https://grafana.com/grafana/dashboards/1860-node-exporter-full/</CodeBlock>
  <figure class="image max-1024">
    <img src={surl('/assets/guides/grafana/10_import_by_url.png')} alt="Import by URL" loading="lazy" />
  </figure>

  <p><span class="step-title"></span>
    Select
    <span class="is-family-monospace notranslate">prometheus</span>
    from the data source options. Then click the
    <span class="has-text-weight-bold">Import</span>
    button to complete the import process.
  </p>
  <figure class="image max-1024">
    <img src={surl('/assets/guides/grafana/11_confirm_import.png')} alt="Confirm Import" loading="lazy" />
  </figure>

  <p><span class="step-title"></span>
    Machine metrics can now be viewed on the imported Node Exporter dashboard.
  </p>
  <figure class="image max-1024">
    <img src={surl('/assets/guides/grafana/12_node_dashboard.png')} alt="Node Dashboard" loading="lazy" />
  </figure>

  <p><span class="step-title"></span>
    You can explore metrics and build your own dashboards in the
    <span class="has-text-weight-bold">Explore &gt; Metrics</span>
    section. Find ServerJockey specific metrics using the labels as shown below. Note that the
    <span class="has-text-weight-bold">process</span>
    label has the ServerJockey instance names, also
    <span class="is-family-monospace notranslate">serverjockey</span>
    for the ServerJockey process itself and
    <span class="is-family-monospace notranslate">serverlink</span>
    for the Discord bot.
  </p>
  <figure class="image max-1024">
    <img src={surl('/assets/guides/grafana/13_explore_metrics.png')} alt="Explore Metrics" loading="lazy" />
  </figure>
</div>

<BackToTop />
