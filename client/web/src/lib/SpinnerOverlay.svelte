<div class="spinner"></div>


<style>
  .spinner {
    width: calc(5vw + 60px);
    height: calc(5vw + 60px);
    border: 18px solid #FFFDF8;
    border-top: 18px solid #00D1B2;
    border-radius: 50%;
    animation: spin 2s linear infinite;
  }

  @keyframes spin {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
  }
</style>
