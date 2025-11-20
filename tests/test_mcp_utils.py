import unittest
import sys
import json
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))
from core_lib.tracing import parse_from
from core_lib.mcp_utils import get_transport_from_args

class TestMcpUtils(unittest.TestCase):
    def test_parse_from_dict(self):
        d = {'foo': 1}
        self.assertEqual(parse_from(d), d)

    def test_parse_from_json_str(self):
        s = '{"foo": 1}'
        self.assertEqual(parse_from(s), {'foo': 1})

    def test_parse_from_invalid(self):
        self.assertEqual(parse_from(None), {})
        self.assertEqual(parse_from(123), {})
        self.assertEqual(parse_from('{bad json}'), {})

    def test_get_transport_from_args(self):
        orig_argv = sys.argv
        sys.argv = ['prog', '--transport=stdio']
        self.assertEqual(get_transport_from_args(), 'stdio')
        sys.argv = ['prog', '--transport=sse']
        self.assertEqual(get_transport_from_args(), 'sse')
        sys.argv = ['prog', '--transport=streamable-http']
        self.assertEqual(get_transport_from_args(), 'streamable-http')
        sys.argv = ['prog']
        self.assertIsNone(get_transport_from_args())
        sys.argv = orig_argv

if __name__ == '__main__':
    unittest.main()
