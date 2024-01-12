<script>
  export let clazz = 'fa fa-spinner fa-lg mr-1';
</script>


<i class="spinner {clazz}"></i>


<style>
  .spinner {
    animation: spin 4s linear infinite;
  }

  @keyframes spin {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
  }
</style>
