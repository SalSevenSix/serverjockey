import assert from 'assert';
import { isBoolean } from 'common/util/util';

describe('isBoolean()', function() {
  it('true if actually true', function() { assert.strictEqual(isBoolean(true), true); });
  it('true if actually false', function() { assert.strictEqual(isBoolean(false), true); });
  it('false if string "true"', function() { assert.strictEqual(isBoolean('true'), false); });
  it('false if string "false"', function() { assert.strictEqual(isBoolean('false'), false); });
  it('false if number 0', function() { assert.strictEqual(isBoolean(0), false); });
  it('false if number 1', function() { assert.strictEqual(isBoolean(1), false); });
});
