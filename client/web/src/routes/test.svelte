<script>
	import { onMount } from 'svelte';
	//let url = 'https://api.coindesk.com/v1/bpi/currentprice.json';
	//let url = 'https://svelte.dev/tutorial/api/album';
	let url = 'http://localhost:6164/instances';
	let text;
	onMount(async () => {
		const result = await fetch(url)
		  .then(function(response) { return response.json(); })
		  .catch(function(error) { return 'Error ' + error; });
		text = JSON.stringify(result);
	});
</script>

<h1>TEST</h1>
<pre>{text}</pre>
