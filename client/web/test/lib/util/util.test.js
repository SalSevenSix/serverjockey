import assert from 'assert';
import { fTrue } from '../../../src/lib/util/util';

describe('fTrue()', function() {
  it('return true', function() { assert.strictEqual(fTrue(), true); });
});
