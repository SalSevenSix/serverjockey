<script>
  import { scrollto } from 'svelte-scrollto-next';
  import { surl } from '$lib/util/sjgmsapi';
  import PrometheusIcon from '$lib/svg/PrometheusIcon.svelte';
  import BackToTop from '$lib/widget/BackToTop.svelte';
  import ExtLink from '$lib/widget/ExtLink.svelte';
  import CodeBlock from '$lib/widget/CodeBlock.svelte';
  import NanoGuide from '$lib/widget/NanoGuide.svelte';
</script>


<div class="columns">
  <div class="column is-one-quarter content mb-0 pb-0">
    <figure class="image mt-2 max-200"><PrometheusIcon /></figure>
  </div>
  <div class="column is-three-quarters content">
    <h2 class="title is-3 mt-2">Monitoring with Prometheus</h2>
    <p>
      <ExtLink href="https://prometheus.io" notranslate>Prometheus</ExtLink>
      is a popular open-source monitoring system. ServerJockey can be integrated as a metrics scrape target.
      This guide will show how to install and configure Prometheus to monitor machine health and game servers
      managed by ServerJockey. Prequisites are a user with root privilages (i.e.
      <span class="is-family-monospace notranslate">sudo</span>)
      and terminal access to the machine with familiarity using it.
    </p>
  </div>
</div>

<div class="content">
  <hr />
  <p><span class="step-title"></span>
    First step is to create a system user for Prometheus to run under. Also added the user to the
    <span class="is-family-monospace notranslate">sjgms</span>
    user group so it can read files from that home directory.
  </p>
  <CodeBlock>sudo adduser --system --home /home/prometheus --disabled-login --disabled-password prometheus</CodeBlock>
  <CodeBlock>sudo usermod -a -G $(ls -ld /home/sjgms | awk &#39;&#123;print $4&#125;&#39;) prometheus</CodeBlock>

  <p><span class="step-title"></span>
    Download and upack Prometheus into its home directory. Note that these commands install version
    <span class="is-family-monospace notranslate">2.52.0</span>
    of Prometheus. Please check the
    <ExtLink href="https://prometheus.io/download/">downloads</ExtLink>
    page to find the latest version.
  </p>
  <CodeBlock>wget https://github.com/prometheus/prometheus/releases/download/v2.52.0/prometheus-2.52.0.linux-amd64.tar.gz</CodeBlock>
  <CodeBlock>tar -xzvf prometheus-2.52.0.linux-amd64.tar.gz &amp;&amp; sudo mv prometheus-2.52.0.linux-amd64 /home/prometheus/prometheus</CodeBlock>

  <p><span class="step-title"></span>
    Prometheus itself just gathers, stores and reports metrics. It does not generate metrics,
    so Node Exporter is required for machine metrics. Again, check
    <ExtLink href="https://prometheus.io/download/#node_exporter">downloads</ExtLink>
    for the latest version.
  </p>
  <CodeBlock>wget https://github.com/prometheus/node_exporter/releases/download/v1.8.1/node_exporter-1.8.1.linux-amd64.tar.gz</CodeBlock>
  <CodeBlock>tar -xzvf node_exporter-1.8.1.linux-amd64.tar.gz &amp;&amp; sudo mv node_exporter-1.8.1.linux-amd64 /home/prometheus/node_exporter</CodeBlock>

  <p><span class="step-title"></span>
    To finish the file install process, set the correct user and group for the prometheus home directory.
  </p>
  <CodeBlock>sudo chown -R prometheus:$(ls -ld /home/prometheus | awk &#39;&#123;print $4&#125;&#39;) /home/prometheus</CodeBlock>

  <p><span class="step-title"></span>
    Now setup Prometheus as a systemd service. <NanoGuide>to create the service file.</NanoGuide>
    Copy, paste and save the service configuration as shown below.
  </p>
  <CodeBlock>sudo nano /etc/systemd/system/prometheus.service</CodeBlock>
  <CodeBlock>
[Unit]
Description=Prometheus Server
Requires=network.target
After=network.target

[Service]
Type=simple
User=prometheus
Restart=on-failure
ExecStart=/home/prometheus/prometheus/prometheus \
  --config.file=/home/prometheus/prometheus/prometheus.yml \
  --storage.tsdb.path=/home/prometheus/data \
  --storage.tsdb.retention.time=30d

[Install]
WantedBy=multi-user.target</CodeBlock>

  <p><span class="step-title"></span>
    Create a systemd service file for Node Exporter too.
    Copy, paste and save the service configuration as shown below.
  </p>
  <CodeBlock>sudo nano /etc/systemd/system/node_exporter.service</CodeBlock>
  <CodeBlock>
[Unit]
Description=Prometheus Node Exporter
Requires=network.target
After=network.target

[Service]
Type=simple
User=prometheus
Restart=on-failure
ExecStart=/home/prometheus/node_exporter/node_exporter

[Install]
WantedBy=multi-user.target</CodeBlock>

  <p><span class="step-title"></span>
    With the service files created, signal systemd to load and apply all service files.
  </p>
  <CodeBlock>sudo systemctl daemon-reload</CodeBlock>

  <p><span class="step-title"></span>
    Enable and start the Prometheus service.
    When enabled, the service will automatically start when the machine starts.
  </p>
  <CodeBlock>sudo systemctl enable prometheus</CodeBlock>
  <CodeBlock>sudo systemctl start prometheus</CodeBlock>
  <p><span class="has-text-weight-bold">Hint:</span>
    At any time you can check the status of the Prometheus service to see if it&#39;s running.
  </p>
  <CodeBlock>sudo systemctl status prometheus</CodeBlock>

  <p><span class="step-title"></span>
    Enable and start the Node Exporter service too.
  </p>
  <CodeBlock>sudo systemctl enable node_exporter</CodeBlock>
  <CodeBlock>sudo systemctl start node_exporter</CodeBlock>

  <p><span class="step-title"></span>
    Finally, Prometheus can now be configured to scrape metrics from both Node Exporter and ServerJockey.
    Open the configuration file in a text editor and find the
    <span class="is-family-monospace notranslate">scrape_configs</span>
    section at the end. Replace that whole section with the configuration shown below.
  </p>
  <CodeBlock>sudo nano /home/prometheus/prometheus/prometheus.yml</CodeBlock>
  <CodeBlock>
scrape_configs:
  # The job name is added as a label &#96;job=<job_name>&#96; to any timeseries scraped from this config.
  - job_name: &quot;prometheus&quot;
    # metrics_path defaults to &#39;/metrics&#39;
    # scheme defaults to &#39;http&#39;.
    static_configs:
      - targets: [&quot;localhost:9090&quot;]
  - job_name: &quot;node&quot;
    static_configs:
      - targets: [&quot;localhost:9100&quot;]
  - job_name: &quot;serverjockey&quot;
    static_configs:
      - targets: [&quot;localhost:6164&quot;]
    basic_auth:
      username: &quot;admin&quot;
      password_file: &quot;/home/sjgms/serverjockey-token.text&quot;</CodeBlock>

  <p><span class="step-title"></span>
    Restart the Prometheus service for the configuration changes to take effect.
    Also check the service status to make sure it actually started.
  </p>
  <CodeBlock>sudo systemctl restart prometheus</CodeBlock>

  <p><span class="step-title"></span>
    To confirm the everything is working, open the Prometheus console in a browser using the machine IP or hostname.
    By default Prometheus uses http listening on port
    <span class="is-family-monospace">9090</span>
    without any authentication. Find the scrape targets status page in the menu under
    <span class="has-text-weight-bold">Status &gt; Targets</span>.
    On this page you should find Node Exporter, ServerJockey and Prometheus itself as active scrape targets.
    <br /><span class="has-text-weight-bold">e.g.</span>&nbsp;
    <span class="is-family-monospace">http://192.168.1.5:9090/targets</span>
  </p>
  <figure class="image max-1024">
    <img src={surl('/assets/guides/prometheus/targets_status.png')} alt="Prometheus Targets Status Page" />
  </figure>
</div>

<div class="content">
  <hr />
  <h4 class="title is-5">So what next?</h4>
  <p>
    ...
    <a href={surl('/guides/grafana')}>Grafana guide</a>
  </p>
</div>

<BackToTop />
