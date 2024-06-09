<script>
  import { scrollto } from 'svelte-scrollto-next';
  import { surl } from '$lib/util/sjgmsapi';
  import PrometheusIcon from '$lib/svg/PrometheusIcon.svelte';
  import BackToTop from '$lib/widget/BackToTop.svelte';
  import ExtLink from '$lib/widget/ExtLink.svelte';
  import CodeBlock from '$lib/widget/CodeBlock.svelte';
</script>


<div class="columns">
  <div class="column is-one-quarter content mb-0 pb-0">
    <figure class="image mt-2 max-200"><PrometheusIcon /></figure>
  </div>
  <div class="column is-three-quarters content">
    <h2 class="title is-3 mt-2">Monitoring with Prometheus</h2>
    <p>
      TODO
      <ExtLink href="https://prometheus.io" notranslate>Prometheus</ExtLink>
    </p>
  </div>
</div>

<div class="content">
  <hr />
  <p><span class="step-title"></span>
    todo
  </p>
  <CodeBlock>sudo adduser --system --home /home/prometheus --disabled-login --disabled-password prometheus</CodeBlock>
  <CodeBlock>sudo usermod -a -G sjgms prometheus</CodeBlock>

  <p><span class="step-title"></span>
    todo
  </p>
  <CodeBlock>wget https://github.com/prometheus/prometheus/releases/download/v2.52.0/prometheus-2.52.0.linux-amd64.tar.gz</CodeBlock>
  <CodeBlock>tar -xzvf prometheus-2.52.0.linux-amd64.tar.gz &amp;&amp; sudo mv prometheus-2.52.0.linux-amd64 /home/prometheus/prometheus</CodeBlock>

  <p><span class="step-title"></span>
    todo
  </p>
  <CodeBlock>wget https://github.com/prometheus/node_exporter/releases/download/v1.8.1/node_exporter-1.8.1.linux-amd64.tar.gz</CodeBlock>
  <CodeBlock>tar -xzvf node_exporter-1.8.1.linux-amd64.tar.gz &amp;&amp; sudo mv node_exporter-1.8.1.linux-amd64 /home/prometheus/node_exporter</CodeBlock>

  <p><span class="step-title"></span>
    todo
  </p>
  <CodeBlock>sudo chown -R prometheus:$(ls -ld /home/prometheus | awk &#39;&#123;print $4&#125;&#39;) /home/prometheus</CodeBlock>

  <p><span class="step-title"></span>
    todo
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
    todo
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
    todo
  </p>
  <CodeBlock>sudo systemctl daemon-reload</CodeBlock>

  <p><span class="step-title"></span>
    todo
  </p>
  <CodeBlock>sudo systemctl enable prometheus</CodeBlock>
  <CodeBlock>sudo systemctl start prometheus</CodeBlock>

  <p><span class="step-title"></span>
    todo
  </p>
  <CodeBlock>sudo systemctl enable node_exporter</CodeBlock>
  <CodeBlock>sudo systemctl start node_exporter</CodeBlock>

  <p><span class="step-title"></span>
    todo
  </p>
  <CodeBlock>sudo nano /home/prometheus/prometheus/prometheus.yml</CodeBlock>
  <CodeBlock>
# A scrape configuration containing exactly one endpoint to scrape:
# Here it&#39;s Prometheus itself.
scrape_configs:
  # The job name is added as a label &#96;job=<job_name>&#96; to any timeseries scraped from this config.
  - job_name: &quot;prometheus&quot;
    # metrics_path defaults to &#39;/metrics&#39;
    # scheme defaults to &#39;http&#39;.
    static_configs:
      - targets: [&quot;localhost:9090&quot;]</CodeBlock>
  <CodeBlock>
&nbsp;&nbsp;- job_name: &quot;node&quot;
    static_configs:
      - targets: [&quot;localhost:9100&quot;]
  - job_name: &quot;serverjockey&quot;
    static_configs:
      - targets: [&quot;localhost:6164&quot;]
    basic_auth:
      username: &quot;admin&quot;
      password_file: &quot;/home/sjgms/serverjockey-token.text&quot;</CodeBlock>

  <p><span class="step-title"></span>
    todo
  </p>
  <CodeBlock>sudo systemctl restart prometheus</CodeBlock>

  <p><span class="step-title"></span>
    todo
  </p>
  <figure class="image max-1024">
    <img src={surl('/assets/guides/prometheus/cpu_total_example.png')} alt="Prometheus CPU Total example" />
  </figure>
</div>

<BackToTop />
