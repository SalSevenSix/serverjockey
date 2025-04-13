import unittest
from core.util import cmdutil

_EXAMPLE = {
    '_comment_port': 'Specify server port, note port+1 also used',
    '-port': 123,
    '_comment_name': 'Name of your server that will be visible in the server listing',
    '-name': 'Myme',
    '_comment_password': 'Optional password needed by players to join server',
    '-pass': None,
    '-foofy': 0,
    '-xplay': True,
    '-preset': False,
    '-modifier': {
        '_comment_combat': 'Options: "veryeasy", "easy", "hard", "veryhard"',
        'combat': None,
        'penalty': 1,
        'resources': 'more'
    }
}


class TestCoreUtilCmdutil(unittest.TestCase):

    def test_append_struct(self):
        cmdline = cmdutil.CommandLine('script.sh')
        cmdline.append('-foo').append('bar').append_struct(_EXAMPLE)
        self.assertEqual(
            'script.sh -foo bar -port 123 -name Myme -foofy 0 -xplay -modifier penalty 1 -modifier resources more',
            cmdline.build_str())
        cmdline = cmdutil.CommandLine('script.sh')
        cmdline.append('-foo=bar').append_struct(_EXAMPLE, '=')
        self.assertEqual(
            'script.sh -foo=bar -port=123 -name=Myme -foofy=0 -xplay -modifierpenalty=1 -modifierresources=more',
            cmdline.build_str())
