<script>
  import { securityToken } from '$lib/serverjockeyapi';

  let value = '';
	function apply() {
	  securityToken.set(value);
	}
</script>


<div>
  <p>Enter token: <input style="width: 50%" bind:value={value} /></p>
  <button id="apply" name="apply" on:click={apply}>Apply</button>
</div>
