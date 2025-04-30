import assert from 'assert';
import { getFirstKey, commandLineToList, clobCommandLine, listifyRoles, chunkStringArray } from '../src/util/util.js';

describe('getFirstKey()', function() {
  const obj = { 'aaa': 3, 'bbb': 2, 'ccc': 1 };
  it('null on null', function() { assert.strictEqual(getFirstKey(null), null); });
  it('null on empty', function() { assert.strictEqual(getFirstKey({}), null); });
  it('first key is first', function() { assert.strictEqual(getFirstKey(obj), 'aaa'); });
});

describe('commandLineToList()', function() {
  it('null value', function() { assert.deepEqual(commandLineToList(null), []); });
  it('empty value', function() { assert.deepEqual(commandLineToList(''), []); });
  it('simple', function() { assert.deepEqual(commandLineToList('aaa bbb ccc'), ['aaa', 'bbb', 'ccc']); });
  it('lines', function() { assert.deepEqual(commandLineToList('aaa\nbbb\nccc'), ['aaa', 'bbb', 'ccc']); });
  it('double q', function() { assert.deepEqual(commandLineToList('aaa "bb cc" ddd'), ['aaa', 'bb cc', 'ddd']); });
  it('single q', function() { assert.deepEqual(commandLineToList("aaa 'bb cc' ddd"), ['aaa', "'bb", "cc'", 'ddd']); });
  it('numbers', function() { assert.deepEqual(commandLineToList('12 34 56'), ['12', '34', '56']); });
});

describe('clobCommandLine()', function() {
  it('empty value', function() { assert.deepEqual(clobCommandLine([]), []); });
  it('no clob', function() { assert.deepEqual(clobCommandLine(['a', 'b=c', 'd=e']), ['a', 'b=c', 'd=e']); });
  it('clobbing', function() { assert.deepEqual(clobCommandLine(['a', 'b=', 'c', 'd=e']), ['a', 'b=c', 'd=e']); });
});

describe('listifyRoles()', function() {
  it('null value', function() { assert.deepEqual(listifyRoles(null), []); });
  it('empty value', function() { assert.deepEqual(listifyRoles(''), []); });
  it('ws value', function() { assert.deepEqual(listifyRoles('   '), []); });
  it('one', function() { assert.deepEqual(listifyRoles('foo'), ['foo']); });
  it('one spaces', function() { assert.deepEqual(listifyRoles(' foo '), ['foo']); });
  it('one at', function() { assert.deepEqual(listifyRoles('@foo'), ['foo']); });
  it('two at', function() { assert.deepEqual(listifyRoles('@foo @bar'), ['foo', 'bar']); });
  it('two at spaces', function() { assert.deepEqual(listifyRoles(' @foo@bar '), ['foo', 'bar']); });
  it('two odd', function() { assert.deepEqual(listifyRoles('foo @bar'), ['foo', 'bar']); });
  it('lots', function() { assert.deepEqual(listifyRoles('@aa @bb @cc @dd @ee'), ['aa', 'bb', 'cc', 'dd', 'ee']); });
});

describe('chunkStringArray()', function() {
  it('null on null', function() { assert.deepEqual(chunkStringArray(null), null); });
  it('null on empty', function() { assert.deepEqual(chunkStringArray(''), [['']]); });
  it('null on zero', function() { assert.deepEqual(chunkStringArray([]), []); });
  it('single', function() { assert.deepEqual(chunkStringArray(['123'], 8), [['123']]); });
  it('single oversize', function() { assert.deepEqual(chunkStringArray(['123456'], 4), [['123456']]); });
  it('first oversize', function() { assert.deepEqual(chunkStringArray(
    ['12345', '67', '8'], 5), [['12345'], ['67', '8']]); });
  it('simple nochunk', function() { assert.deepEqual(chunkStringArray(
    ['123', '456', 'abc'], 3), [['123'], ['456'], ['abc']]); });
  it('simple chunking', function() { assert.deepEqual(chunkStringArray(
    ['123', '456', 'abc', 'def', 'xyz'], 8), [['123', '456'], ['abc', 'def'], ['xyz']]); });
});
