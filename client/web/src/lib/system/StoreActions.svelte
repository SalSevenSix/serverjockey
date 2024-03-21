<script>
  import { newPostRequest } from '$lib/util/sjgmsapi';
  import { notifyInfo, notifyError } from '$lib/util/notifications';
  import { confirmModal } from '$lib/modal/modals';

  let processing = false;

  function actionResetActivity() {
    const actionName = this.name;
    const actionTitle = this.title;
    confirmModal('Are you sure you want to ' + actionTitle + ' ?\nThis action cannot be undone.', function() {
      processing = true;
      fetch('/store/' + actionName, newPostRequest())
        .then(function(response) {
          if (!response.ok) throw new Error('Status: ' + response.status);
          notifyInfo(actionTitle + ' completed.');
        })
        .catch(function(error) { notifyError(actionTitle + ' failed.'); })
        .finally(function() { processing = false; });
    });
  }
</script>


<div class="block pb-4">
  <table class="table">
    <tbody>
      <tr>
        <td>
          <button name='reset' title='Reset Activity' class="button is-danger is-fullwidth"
                  disabled={processing} on:click={actionResetActivity}>
            <i class="fa fa-explosion fa-lg"></i>&nbsp; Reset Activity</button>
        </td>
        <td>Delete all recorded Instance, Player and Chat activity from storage.</td>
      </tr>
    </tbody>
  </table>
</div>
