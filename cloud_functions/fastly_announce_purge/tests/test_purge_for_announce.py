import base64
import unittest
from unittest.mock import patch, call
from cloudevents.http import CloudEvent

import sys, os
sys.path.append( os.path.join(os.path.dirname(__file__), "..", "src") )
from main import purge_for_announce

class TestAnnouncePurge(unittest.TestCase):
    production_calls = [
        call("announce", "rss.arxiv.org"),
        call("announce" ),
        call("announce","export.arxiv.org")
    ]
    dev_calls=[call("announce", "browse.dev.arxiv.org"),]

    mock_data = {
        "message": {
            "data": base64.b64encode(b'{"event": "announcement_complete"}')
        }
    }
    announce_cloud_event = CloudEvent({'type': 'test', 'source': 'test'}, mock_data)

    mock_data2 = {
        "message": {
            "data": base64.b64encode(b'{"event": "other_event"}')
        }
    }
    other_cloud_event = CloudEvent({'type': 'test', 'source': 'test'}, mock_data2)

    @patch('main.purge_fastly_keys')
    def test_nonsense_environment(self, MockPurgeFun):
        with patch.dict('os.environ', {'ENVIRONMENT': 'Nonsense'}):
            purge_for_announce(self.announce_cloud_event)
            MockPurgeFun.assert_not_called()

    @patch('main.purge_fastly_keys')
    def test_wrong_event(self, MockPurgeFun):
        with patch.dict('os.environ', {'ENVIRONMENT': 'PRODUCTION'}):
            purge_for_announce(self.other_cloud_event)
            MockPurgeFun.assert_not_called()

    @patch('main.purge_fastly_keys')
    def test_production_calls(self, MockPurgeFun):
        with patch.dict('os.environ', {'ENVIRONMENT': 'PRODUCTION'}):
            purge_for_announce(self.announce_cloud_event)
            MockPurgeFun.assert_has_calls(self.production_calls, any_order=True)
            for call in self.dev_calls:
                assert call not in MockPurgeFun.call_args_list
            
    @patch('main.purge_fastly_keys')
    def test_development_calls(self, MockPurgeFun):
        with patch.dict('os.environ', {'ENVIRONMENT': 'DEVELOPMENT'}):
            purge_for_announce(self.announce_cloud_event)
            MockPurgeFun.assert_has_calls(self.dev_calls, any_order=True)
            for call in self.production_calls:
                assert call not in MockPurgeFun.call_args_list

    