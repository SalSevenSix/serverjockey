import * as logger from '../util/logger.js';

export function newCooldowns() {
  const [interval, cooldown, queue] = [1000, 30000, []];
  let [processing, duration] = [false, cooldown];

  const process = async function() {
    const callback = queue.shift();
    const success = await callback();
    if (success) { duration = 0; }
  };

  const tick = function() {
    if (processing) return;
    if (duration < cooldown) {
      duration += interval;
    } else if (queue.length > 0) {
      processing = true;
      process().catch(logger.error).finally(function() {
        processing = false;
      });
    }
  };

  const [self, timer] = [{}, setInterval(tick, interval)];
  self.shutdown = function() { clearInterval(timer); };
  self.submit = function(callback) { queue.push(callback); };
  return self;
}
