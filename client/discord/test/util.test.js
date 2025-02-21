import assert from 'assert';
import { getFirstKey } from '../src/util';

describe('getFirstKey()', function() {
  const obj = { 'aaa': 3, 'bbb': 2, 'ccc': 1 };
  it('null on null', function() { assert.strictEqual(getFirstKey(null), null); });
  it('null on empty', function() { assert.strictEqual(getFirstKey({}), null); });
  it('first key is first', function() { assert.strictEqual(getFirstKey(obj), 'aaa'); });
});
