import assert from 'assert';
import { fTrue, generateId, guessTextFile, chunkArray,
         capitalize, toCamelCase, capitalizeKebabCase } from '../../../src/lib/util/util.js';

describe('fTrue()', function() {
  it('return true', function() { assert.strictEqual(fTrue(), true); });
});

describe('generateId()', function() {
  const gid = generateId();
  it('is unique', function() { assert.strictEqual(gid === generateId(), false); });
  it('length over 26', function() { assert.strictEqual(gid.length > 26, true); });
  it('numbers only', function() { assert.strictEqual((/^\d*$/).test(gid), true); });
});

describe('capitalize()', function() {
  it('null value', function() { assert.strictEqual(capitalize(null), ''); });
  it('empty value', function() { assert.strictEqual(capitalize(''), ''); });
  it('simple', function() { assert.strictEqual(capitalize('helLo woRld'), 'HelLo woRld'); });
});

describe('toCamelCase()', function() {
  it('null value', function() { assert.strictEqual(toCamelCase(null), ''); });
  it('empty value', function() { assert.strictEqual(toCamelCase(''), ''); });
  it('simple', function() { assert.strictEqual(toCamelCase('helLo woRld'), 'HelLoWoRld'); });
});

describe('capitalizeKebabCase()', function() {
  it('null value', function() { assert.strictEqual(capitalizeKebabCase(null), ''); });
  it('empty value', function() { assert.strictEqual(capitalizeKebabCase(''), ''); });
  it('simple', function() { assert.strictEqual(capitalizeKebabCase('hello-world'), 'Hello World'); });
  it('complex', function() { assert.strictEqual(capitalizeKebabCase('hello-world hiya'), 'Hello World hiya'); });
});

describe('chunkArray()', function() {
  it('null value', function() { assert.deepEqual(chunkArray(null), []); });
  it('few', function() { assert.deepEqual(chunkArray([1, 2, 3], 5, 3), [[1, 2, 3], [], []]); });
  const sample = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13];
  let expected = [[1, 2, 3, 4, 5], [6, 7, 8, 9, 10], [11, 12, 13]];
  it('under', function() { assert.deepEqual(chunkArray(sample, 5, 3), expected); });
  sample.push(14);
  sample.push(15);
  expected = [[1, 2, 3, 4, 5], [6, 7, 8, 9, 10], [11, 12, 13, 14, 15]];
  it('filled', function() { assert.deepEqual(chunkArray(sample, 5, 3), expected); });
  sample.push(16);
  sample.push(17);
  expected = [[1, 2, 3, 4, 5, 6], [7, 8, 9, 10, 11, 12], [13, 14, 15, 16, 17]];
  it('over', function() { assert.deepEqual(chunkArray(sample, 5, 3), expected); });
});

describe('guessTextFile()', function() {
  it('null value', function() { assert.strictEqual(guessTextFile(null), false); });
  it('empty value', function() { assert.strictEqual(guessTextFile(''), false); });
  it('name plain', function() { assert.strictEqual(guessTextFile('file'), false); });
  it('folder plain', function() { assert.strictEqual(guessTextFile('/path/file'), false); });
  it('name keyword', function() { assert.strictEqual(guessTextFile('text'), false); });
  it('folder keyword', function() { assert.strictEqual(guessTextFile('/path/text'), false); });
  it('file gif', function() { assert.strictEqual(guessTextFile('/path/file.gif'), false); });
  it('file 2ext png', function() { assert.strictEqual(guessTextFile('/path/file.gif.png'), false); });
  it('file 2ext log', function() { assert.strictEqual(guessTextFile('/path/file.gif.log'), true); });
  it('file text', function() { assert.strictEqual(guessTextFile('/path/file.text'), true); });
  it('file log', function() { assert.strictEqual(guessTextFile('/path/file.log'), true); });
  it('file LOG', function() { assert.strictEqual(guessTextFile('/path/file.LOG'), true); });
  it('file log n', function() { assert.strictEqual(guessTextFile('/path/file.log.1'), true); });
  it('file log stamp1', function() { assert.strictEqual(guessTextFile('/path/file.log.123_234-123'), true); });
  it('file log stamp2', function() { assert.strictEqual(guessTextFile('/path/file.log.___'), true); });
  it('file log stamp3', function() { assert.strictEqual(guessTextFile('/path/file.log.---'), true); });
  it('file log prev', function() { assert.strictEqual(guessTextFile('/path/file.log.prev'), true); });
  it('file log Prev', function() { assert.strictEqual(guessTextFile('/path/file.log.Prev'), true); });
  it('file log previous', function() { assert.strictEqual(guessTextFile('/path/file.log.previous'), true); });
  it('file log backup', function() { assert.strictEqual(guessTextFile('/path/file.log.backup'), true); });
  it('file log gif', function() { assert.strictEqual(guessTextFile('/path/file.log.gif'), false); });
  it('file log n n', function() { assert.strictEqual(guessTextFile('/path/file.log.1.2'), false); });
});
