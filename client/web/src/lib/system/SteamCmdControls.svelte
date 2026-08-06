<script>
  import { surl, newPostRequest, getReponseJson } from '$lib/util/sjgmsapi';
  import { notifyInfo, notifyWarning, notifyError } from '$lib/util/notifications';
  import { confirmModal } from '$lib/modal/modals';

  let processing = false;

  function reset() {
    confirmModal('Are you sure you want to reset SteamCMD ?', function() {
      processing = true;
      fetch(surl('/system/steamcmd/reset'), newPostRequest())
        .then(function(response) { return getReponseJson(response); })
        .then(function(json) {
          if (json.status) { notifyInfo(json.text); }
          else { notifyWarning(json.text); }
        })
        .catch(function() { notifyError('Failed to reset SteamCMD.'); })
        .finally(function() { processing = false; });
    });
  }
</script>


<div class="columns">
  <div class="column is-one-quarter">
    <button id="resetSteamCmd" class="button is-warning" title="Reset SteamCMD" disabled={processing} on:click={reset}>
      <i class="fa-brands fa-steam fa-lg"></i>&nbsp; Reset</button>
  </div>
  <div class="column is-three-quarters">
    Reset SteamCMD to clear cache and force it to reinstall. Use this to try fix problems with SteamCMD failing
    to install or update game servers, installing incorrect server version, or any other issues.
    Consider deleting game server (runtime) and do a fresh install if problems persist after SteamCMD reset.
  </div>
</div>
