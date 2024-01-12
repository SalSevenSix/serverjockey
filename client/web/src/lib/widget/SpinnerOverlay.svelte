
<div class="overlay"><div class="inner"><div class="spinner"></div></div></div>


<style>
  .overlay {
    position: absolute;
    width: 100%;
    height: 100%;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background-color: rgba(0,0,0,0.3);
    z-index: 10;
  }

  .inner {
    padding-top: 15vh;
    padding-left: 30%;
  }

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
