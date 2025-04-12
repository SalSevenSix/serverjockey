import unittest
from core.util import linenc

# https://en.wikipedia.org/wiki/ANSI_escape_code
# https://gist.github.com/fnky/458719343aabd01cfb17a3a4f7296797


class TestCoreProcPtyLineDecoder(unittest.TestCase):

    def test_ansi_control_characters_are_removed(self):
        d = linenc.PtyLineDecoder()
        self.assertEqual('', d.decode(b''))
        self.assertEqual('Just Plain Text', d.decode(b'Just Plain Text'))
        self.assertEqual('bold text reset all', d.decode(b'\x1B[1mbold text reset all\x1B[0m'))
        self.assertEqual('colour red', d.decode(b'\x1B[31mcolour red'))
        self.assertEqual('colour white', d.decode(b'\x1B[37mcolour white'))
        self.assertEqual('request cursor position', d.decode(b'\x1B[6nrequest cursor position'))
        self.assertEqual('=0;Unturned', d.decode(b'\x1B[?1h\x1B=\x1B[6n\x1B[H\x1B[2J\x1B]0;Unturned'))
        self.assertEqual('ServerJockeyDev Successfully set name', d.decode(b'ServerJockeyDev\x07Successfully set name'))
        self.assertEqual('>', d.decode(b'\x1B[?1l\x1B>\x1B[39;49m'))
