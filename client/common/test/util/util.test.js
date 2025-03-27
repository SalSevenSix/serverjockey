import assert from 'assert';
import { isBoolean, isString, urlSafeB64encode, floatToPercent, moveArrayElement, humanDuration, humanFileSize,
         shortISODateTimeString, parseDateToMillis, presetDate, rangeCodeToMillis,
         newArrayBuilder } from 'common/util/util';

describe('isBoolean()', function() {
  it('true if actually true', function() { assert.strictEqual(isBoolean(true), true); });
  it('true if actually false', function() { assert.strictEqual(isBoolean(false), true); });
  it('false if string "true"', function() { assert.strictEqual(isBoolean('true'), false); });
  it('false if string "false"', function() { assert.strictEqual(isBoolean('false'), false); });
  it('false if number 0', function() { assert.strictEqual(isBoolean(0), false); });
  it('false if number 1', function() { assert.strictEqual(isBoolean(1), false); });
});

describe('isString()', function() {
  it('false if null', function() { assert.strictEqual(isString(null), false); });
  it('false if number', function() { assert.strictEqual(isString(123), false); });
  it('true if empty', function() { assert.strictEqual(isString(''), true); });
  it('true if string', function() { assert.strictEqual(isString('foo'), true); });
});

describe('urlSafeB64encode()', function() {
  const actual = urlSafeB64encode('So?<p> $ – _ . + ! * ‘ ( ) , [ ] { } | \\ " % ~ # < >');
  const expected = 'U28_PHA-ICQg4oCTIF8gLiArICEgKiDigJggKCApICwgWyBdIHsgfSB8IFwgIiAlIH4gIyA8ID4=';
  it('encoded correctly', function() { assert.strictEqual(actual, expected); });
});

describe('floatToPercent()', function() {
  it('null is 0.0%', function() { assert.strictEqual(floatToPercent(null), '0.0%'); });
  it('0.0 is 0.0%', function() { assert.strictEqual(floatToPercent(0.0), '0.0%'); });
  it('0.1234 is 12.3%', function() { assert.strictEqual(floatToPercent(0.1234), '12.3%'); });
  it('0.1235 is 12.4%', function() { assert.strictEqual(floatToPercent(0.1235), '12.3%'); });
  it('0.1236 is 12.4%', function() { assert.strictEqual(floatToPercent(0.1236), '12.4%'); });
  it('1.0 is 100.0%', function() { assert.strictEqual(floatToPercent(1.0), '100.0%'); });
  it('2.3452 is 234.5%', function() { assert.strictEqual(floatToPercent(2.3452), '234.5%'); });
  it('args used', function() { assert.strictEqual(floatToPercent(0.1234567, 3, ' pc'), '12.346 pc'); });
});

describe('moveArrayElement()', function() {
  const sample = [1, 2, 3, 4, 5];
  it('null array', function() { assert.strictEqual(moveArrayElement(null, null, null), null); });
  it('invalid args', function() { assert.deepEqual(moveArrayElement(sample, null, null), [1, 2, 3, 4, 5]); });
  it('no position change', function() { assert.deepEqual(moveArrayElement(sample, 2, 0), [1, 2, 3, 4, 5]); });
  it('bump up', function() { assert.deepEqual(moveArrayElement(sample, 3, -2), [1, 4, 2, 3, 5]); });
  it('bump down', function() { assert.deepEqual(moveArrayElement(sample, 1, 2), [1, 3, 4, 2, 5]); });
  it('beyond index 0', function() { assert.deepEqual(moveArrayElement(sample, 1, -2), [2, 1, 3, 4, 5]); });
  it('beyond index length', function() { assert.deepEqual(moveArrayElement(sample, 3, 2), [1, 2, 3, 5, 4]); });
  it('string args', function() { assert.deepEqual(moveArrayElement(sample, '0', '3'), [2, 3, 4, 1, 5]); });
});

describe('humanFileSize()', function() {
  const [kb, mb, gb] = [1024, 1024 * 1024, 1024 * 1024 * 1024];
  it('null value', function() { assert.strictEqual(humanFileSize(null), ''); });
  it('0 bytes', function() { assert.strictEqual(humanFileSize(0), '0 B'); });
  it('max bytes', function() { assert.strictEqual(humanFileSize(kb - 1), '1023 B'); });
  it('1 kilobyte', function() { assert.strictEqual(humanFileSize(kb), '1.0 KiB'); });
  it('1 megabyte', function() { assert.strictEqual(humanFileSize(mb), '1.0 MiB'); });
  it('1 gigabyte', function() { assert.strictEqual(humanFileSize(gb), '1.0 GiB'); });
  it('1.5 gigabyte', function() { assert.strictEqual(humanFileSize(gb + mb * 512), '1.5 GiB'); });
  it('more decimal places', function() { assert.strictEqual(humanFileSize(12345678, 3), '11.774 MiB'); });
  it('si types', function() { assert.strictEqual(humanFileSize(1000, 1, true), '1.0 kB'); });
});

describe('humanDuration()', function() {
  const [mm, hh, dd] = [60000, 60000 * 60, 60000 * 60 * 24];
  it('null value', function() { assert.strictEqual(humanDuration(null), ''); });
  it('zero time', function() { assert.strictEqual(humanDuration(0), '0d 0h 0m'); });
  it('1 minute', function() { assert.strictEqual(humanDuration(mm), '0d 0h 1m'); });
  it('1 hour', function() { assert.strictEqual(humanDuration(hh), '0d 1h 0m'); });
  it('1 day', function() { assert.strictEqual(humanDuration(dd), '1d 0h 0m'); });
  it('-1 day', function() { assert.strictEqual(humanDuration(0 - dd), '-1d 0h 0m'); });
  it('1 day, hour, minute', function() { assert.strictEqual(humanDuration(dd + hh + mm), '1d 1h 1m'); });
  it('1 day as hours mins', function() { assert.strictEqual(humanDuration(hh * 32, 'hm'), '32h 0m'); });
  it('1 day as mins secs', function() { assert.strictEqual(humanDuration(hh * 12 + 6, 'ms'), '720m 6s'); });
});

describe('shortISODateTimeString()', function() {
  const sample = 1740205962869;
  it('null value', function() { assert.strictEqual(shortISODateTimeString(null), ''); });
  it('GMT time', function() { assert.strictEqual(shortISODateTimeString(sample, false), '2025-02-22 06:32:42'); });
  it('given tz', function() { assert.strictEqual(shortISODateTimeString(sample, '+7'), '2025-02-22 13:32:42'); });
  it('dt', function() { assert.strictEqual(shortISODateTimeString(new Date(sample), '-7'), '2025-02-21 23:32:42'); });
});

describe('parseDateToMillis()', function() {
  const expected = 1740205962000;
  it('null value', function() { assert.strictEqual(parseDateToMillis(null), null); });
  it('GMT date', function() { assert.strictEqual(parseDateToMillis('2025-02-22 06:32:42', 'GMT'), expected); });
  it('given tz', function() { assert.strictEqual(parseDateToMillis('2025-02-22 13:32:42', '+7'), expected); });
  it('millis value', function() { assert.strictEqual(parseDateToMillis(expected), expected); });
});

describe('presetDate()', function() {
  const sample = new Date(2025, 1, 23, 15, 42, 51, 876);
  it('null values', function() { assert.strictEqual(presetDate(null, null), null); });
  it('null preset', function() { assert.strictEqual(presetDate(sample, null), sample); });
  it('last hour', function() { assert.deepEqual(presetDate(sample, 'LH'), new Date(2025, 1, 23, 15)); });
  it('last day', function() { assert.deepEqual(presetDate(sample, 'LD'), new Date(2025, 1, 23)); });
  it('last month', function() { assert.deepEqual(presetDate(sample, 'LM'), new Date(2025, 1)); });
  it('this month', function() { assert.deepEqual(presetDate(sample, 'TM'), new Date(2025, 2)); });
  it('specific tz', function() {
    assert.deepEqual(presetDate(sample, 'LD', '+7'), new Date('2025-02-22T17:00:00.000Z'));
  });
});

describe('rangeCodeToMillis()', function() {
  const sample = new Date(2025, 1, 23, 15, 42, 51, 876);
  it('null value', function() { assert.strictEqual(rangeCodeToMillis(null), null); });
  it('zero value', function() { assert.strictEqual(rangeCodeToMillis(0), 0); });
  it('int value', function() { assert.strictEqual(rangeCodeToMillis(123), 123); });
  it('neg int value', function() { assert.strictEqual(rangeCodeToMillis(-123), -123); });
  it('zero str', function() { assert.strictEqual(rangeCodeToMillis('0'), 0); });
  it('millis', function() { assert.strictEqual(rangeCodeToMillis('123'), 123); });
  it('neg millis', function() { assert.strictEqual(rangeCodeToMillis('-123'), -123); });
  it('seconds', function() { assert.strictEqual(rangeCodeToMillis('123s'), 123000); });
  it('minutes', function() { assert.strictEqual(rangeCodeToMillis('123m'), 7380000); });
  it('hours', function() { assert.strictEqual(rangeCodeToMillis('123h'), 442800000); });
  it('neg hours', function() { assert.strictEqual(rangeCodeToMillis('-123h'), -442800000); });
  it('days', function() { assert.strictEqual(rangeCodeToMillis('123d'), 10627200000); });
});
