import base64
import unittest
from unittest.mock import patch, call
from cloudevents.http import CloudEvent

import sys, os
sys.path.append( os.path.join(os.path.dirname(__file__), "..", "src") )
from main import purge_all_for_paper

class TestAnnouncePurge(unittest.TestCase):
    mock_data1 = {
        "message": {
            "data": base64.b64encode(b'{"paper_id": "1205.1234", "old_categories": "Not specified"}')
        }
    }
    mock_data2 = {
        "message": {
            "data": base64.b64encode(b'{"paper_id": "1205.1234", "old_categories": "hep-lat cs.NA"}')
        }
    }
    non_cat_cloud_event = CloudEvent({'type': 'test', 'source': 'test'}, mock_data1)
    cat_cloud_event = CloudEvent({'type': 'test', 'source': 'test'}, mock_data2)

    @patch('main.purge_cache_for_paper')
    def test_not_prod_environment(self, MockPurgeFun):
        with patch.dict('os.environ', {'ENVIRONMENT': 'Nonsense'}):
            purge_all_for_paper(self.non_cat_cloud_event)
            MockPurgeFun.assert_not_called()

    @patch('main.purge_cache_for_paper')
    def test_with_old_cats(self, MockPurgeFun):
        with patch.dict('os.environ', {'ENVIRONMENT': 'PRODUCTION'}):
            purge_all_for_paper(self.cat_cloud_event)
            MockPurgeFun.assert_called_once_with("1205.1234","hep-lat cs.NA")

    @patch('main.purge_cache_for_paper')
    def test_no_old_cats(self, MockPurgeFun):
        with patch.dict('os.environ', {'ENVIRONMENT': 'PRODUCTION'}):
            purge_all_for_paper(self.non_cat_cloud_event)
            MockPurgeFun.assert_called_once_with("1205.1234")
