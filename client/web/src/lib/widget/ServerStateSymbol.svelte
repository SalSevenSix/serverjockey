<script>
  import { hasProp } from 'common/util/util';

  export let state;
  export let bigger = false;

  const stateMap = {
    READY: 'fa-stop', STOPPED: 'fa-stop',
    START: 'fa-play status-color-amber', STARTING: 'fa-play status-color-amber',
    STARTED: 'fa-play status-color-green',
    STOPPING: 'fa-stop status-color-amber',
    MAINTENANCE: 'fa-gear status-color-amber',
    EXCEPTION: 'fa-triangle-exclamation status-color-red'
  };

  $: clazz = getClazz(state); function getClazz(value) {
    const result = ['fa'];
    result.push(hasProp(stateMap, value) ? stateMap[value] : 'fa-stop');
    result.push(bigger ? 'fa-xl' : 'fa-lg');
    return result.join(' ');
  }
</script>


<i class={clazz} title={state}></i>
