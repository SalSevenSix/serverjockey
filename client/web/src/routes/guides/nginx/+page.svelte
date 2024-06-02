<script>
  import { scrollto } from 'svelte-scrollto-next';
  import { surl } from '$lib/util/sjgmsapi';
  import NginxIcon from '$lib/svg/NginxIcon.svelte';
  import BackToTop from '$lib/widget/BackToTop.svelte';
  import ExtLink from '$lib/widget/ExtLink.svelte';
  import CodeBlock from '$lib/widget/CodeBlock.svelte';
</script>


<div class="columns">
  <div class="column is-one-quarter content mb-0 pb-0">
    <figure class="image mt-2 max-200"><NginxIcon /></figure>
  </div>
  <div class="column is-three-quarters content">
    <h2 class="title is-3 mt-2">Hosting behind Nginx</h2>
    <p>
      ServerJockey can be hosted behind
      <ExtLink href="https://nginx.org" notranslate>Nginx</ExtLink>
      using its reverse proxy feature. This guide will show how to create this setup.
      It will feature using a domain name, HTTPS with a properly signed SSL certificate,
      HTTP2 support, IPv6 support, and more. Prequisites are a user with root privilages (i.e.
      <span class="is-family-monospace notranslate">sudo</span>)
      and terminal access to the machine with familiarity using it.
    </p>
    <ul>
      <li><a href="#obtaindomain" use:scrollto={'#obtaindomain'}>Obtain a domain name</a>
      <li><a href="#installnginx" use:scrollto={'#installnginx'}>Install Nginx</a>
      <li><a href="#generatesslcert" use:scrollto={'#generatesslcert'}>Generate SSL certificate</a>
      <li><a href="#nginxconfig" use:scrollto={'#nginxconfig'}>Nginx configuration</a>
    </ul>
  </div>
</div>

<div class="content">
  <hr />
  <h3 id="obtaindomain" class="title is-4">Obtain a domain name</h3>
  <p>
    A public internet domain name is used to find a machine on the internet by its IP address.
    You can obtain a domain name from a domain name registry such as <span class="has-text-weight-bold">GoDaddy</span>
    and many others. However you will need to pay a recurring fee to use the domain name.
    Alternatively you can use a dynamic DNS service such as
    <ExtLink href="https://www.duckdns.org" notranslate>Duck DNS</ExtLink>
    which is free to use. This guide uses the domain name
    <span class="is-family-monospace has-text-weight-bold notranslate">example.duckdns.org</span>
    as a placeholder, <span class="is-italic">please make sure you use your own domain name instead!</span>
  </p>
  <p>
    Whatever service you use, ensure that the configured IP address for the domain name is kept up-to-date.
    Note that a domain name can be used with ServerJockey without needing Nginx.
  </p>
  <figure class="image max-1024">
    <img src={surl('/assets/guides/nginx/duckdns_example.png')} alt="DuckDNS example" />
  </figure>

  <h3 id="installnginx" class="title is-4">Install Nginx</h3>
  <p>
    Nginx can be installed using the package manager as shown below.
  </p>
  <CodeBlock>sudo apt install nginx</CodeBlock>
  <p>
    It will be setup as an enabled <span class="notranslate">systemd</span> service and automatically started.
    You can check the status of the Nginx service with the command shown below.
  </p>
  <CodeBlock>sudo systemctl status nginx</CodeBlock>
  <p>
    Now test that the Nginx default welcome page can be accessed over the internet.
    Try to open the website with a browser using the public IP address,
    <span class="is-italic">also your domain name.</span>
    If you have any issues try the following...
  </p>
  <ul>
    <li>Make sure the URL is using HTTP not HTTPS
    <li>Ensure port 80 and 443 are open to the internet for TCP
    <li>If the domain name is not working, check that the correct IP is associated
    <li>Clear browser cache and double check all networking
  </ul>
  <figure class="image max-1024">
    <img src={surl('/assets/guides/nginx/nginx_welcome.png')} alt="Nginx welcome page" loading="lazy" />
  </figure>

  <h3 id="generatesslcert" class="title is-4">Generate SSL certificate</h3>
  <p>
    A domain name and an SSL certificate is required for HTTPS. The certificate must be signed by
    a trusted certificate authority, otherwise browsers will show security warnings to the user.
    Domain name registries often provide a certificate generation service. If that&#39;s not an option then...
  </p>
  <p>
    <ExtLink href="https://letsencrypt.org" notranslate>Let&#39;s Encrypt</ExtLink>
    is nonprofit certificate authority that provides SSL certificates for free.
    <ExtLink href="https://certbot.eff.org" notranslate>Certbot</ExtLink>
    is a command line tool you can use to generate SSL certificates using Let&#39;s Encrypt.
    Check the Certbot website for install options for your machine.
    If <span class="is-family-monospace notranslate">snap</span> is available,
    it&#39;s recommended you install that version with the following command.
  </p>
  <CodeBlock>sudo snap install --classic certbot</CodeBlock>
  <p>
    Make sure Nginx is running with the welcome page accessible over the internet using your domain name.
    Now generate the certificate files with the command shown below using your domain name.
    The process will prompt for an email address and to accept terms &amp; conditions to setup an account.
    Work through the prompts to complete the process.
  </p>
  <CodeBlock>sudo certbot certonly --nginx -d example.duckdns.org</CodeBlock>
  <p>
    If the process was successful, you should find an SSL configuration file for Nginx at the location below.
  </p>
  <CodeBlock>/etc/letsencrypt/options-ssl-nginx.conf</CodeBlock>
  <p>
    The generated certificate files should be found in the folder below, but with your domain name.
  </p>
  <CodeBlock>/etc/letsencrypt/live/example.duckdns.org</CodeBlock>
  <figure class="image max-1024">
    <img src={surl('/assets/guides/nginx/example_cert_files.png')} alt="Example certificate files" loading="lazy" />
  </figure>

  <h3 id="nginxconfig" class="title is-4">Nginx configuration</h3>
  <p>
    Final step is to configure Nginx to use HTTPS, the domain name, the SSL configuration file, the certificate files,
    and to direct http requests to ServerJockey. Use a text editor such as
    <span class="is-family-monospace notranslate">nano</span> to edit the Nginx configuration file.
  </p>
  <CodeBlock>sudo nano /etc/nginx/nginx.conf</CodeBlock>
  <p>
    Below is a single file working example configuration. Replace the entire contents of
    <span class="is-family-monospace notranslate">nginx.conf</span> but
    <span class="is-italic">remember to substitute your domain name.</span>
  </p>
  <CodeBlock>user www-data&#59;
worker_processes 1&#59;
pid /run/nginx.pid&#59;
include /etc/nginx/modules-enabled/*.conf&#59;

events &#123;
  worker_connections 768&#59;
&#125;

http &#123;
  sendfile on&#59;
  tcp_nopush on&#59;
  types_hash_max_size 2048&#59;
  server_tokens off&#59;
  gzip off&#59;

  include /etc/nginx/mime.types&#59;
  default_type application/octet-stream&#59;
  include /etc/letsencrypt/options-ssl-nginx.conf&#59;

  access_log /var/log/nginx/access.log&#59;
  error_log /var/log/nginx/error.log&#59;

  upstream serverjockey &#123;
    server 127.0.0.1&#58;6164&#59;
    keepalive 32&#59;
  &#125;

  server &#123;
    listen 443 ssl http2 default_server&#59;
    listen [&#58;&#58;]&#58;443 ssl http2 ipv6only=on default_server&#59;
    ssl_certificate /etc/letsencrypt/live/example.duckdns.org/fullchain.pem&#59;
    ssl_certificate_key /etc/letsencrypt/live/example.duckdns.org/privkey.pem&#59;

    server_name example.duckdns.org&#59;
    root /var/www/html&#59;
    index index.html&#59;

    location / &#123;
      proxy_pass http&#58;//serverjockey&#59;
      proxy_http_version 1.1&#59;
      proxy_set_header Connection &quot;&quot;&#59;
      proxy_set_header Host $host&#59;
      proxy_set_header X-Real-IP $remote_addr&#59;
      proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for&#59;
      proxy_set_header X-Forwarded-Proto https&#59;
      proxy_read_timeout 90s&#59;
      access_log off&#59;
    &#125;
  &#125;

  server &#123;
    listen 80 default_server&#59;
    listen [&#58;&#58;]&#58;80 default_server&#59;
    server_name _&#59;
    return 301 https&#58;//$host$request_uri&#59;
  &#125;
&#125;</CodeBlock>
  <p>
    Test the Nginx configuration is valid with the command show below.
  </p>
  <CodeBlock>sudo nginx -t</CodeBlock>
  <p>
    Use the command below to signal Nginx to load and apply the updated configuration.
  </p>
  <CodeBlock>sudo nginx -s reload</CodeBlock>
  <p>
    Now open ServerJockey in a browser using HTTPS and your domain name.
  </p>
  <figure class="image max-1024 mt-0">
    <img src={surl('/assets/guides/nginx/proxied_serverjockey.png')} alt="ServerJockey behind Nginx" loading="lazy" />
  </figure>
</div>

<BackToTop />
