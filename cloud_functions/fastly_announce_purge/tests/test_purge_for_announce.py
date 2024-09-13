import base64
import unittest
from unittest.mock import patch, call
from cloudevents.http import CloudEvent

import sys, os
sys.path.append( os.path.join(os.path.dirname(__file__), "..", "src") )
from main import purge_for_announce, _process_announcements

class TestAnnouncePurge(unittest.TestCase):
    production_calls = [
        call("announce", "rss.arxiv.org"),
        call("announce" ),
        #call("announce","export.arxiv.org") #not currently enabled
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
    @patch('main._purge_announced_papers')
    def test_nonsense_environment(self, _, MockPurgeFun):
        with patch.dict('os.environ', {'ENVIRONMENT': 'Nonsense'}):
            purge_for_announce(self.announce_cloud_event)
            MockPurgeFun.assert_not_called()

    @patch('main.purge_fastly_keys')
    def test_wrong_event(self, MockPurgeFun):
        with patch.dict('os.environ', {'ENVIRONMENT': 'PRODUCTION'}):
            purge_for_announce(self.other_cloud_event)
            MockPurgeFun.assert_not_called()

    @patch('main.purge_fastly_keys')
    @patch('main._purge_announced_papers')
    def test_production_calls(self,_, MockPurgeFun):
        with patch.dict('os.environ', {'ENVIRONMENT': 'PRODUCTION'}):
            purge_for_announce(self.announce_cloud_event)
            MockPurgeFun.assert_has_calls(self.production_calls, any_order=True)
            for call in self.dev_calls:
                assert call not in MockPurgeFun.call_args_list
            
    @patch('main.purge_fastly_keys')
    @patch('main._purge_announced_papers')
    def test_development_calls(self,_, MockPurgeFun):
        with patch.dict('os.environ', {'ENVIRONMENT': 'DEVELOPMENT'}):
            purge_for_announce(self.announce_cloud_event)
            MockPurgeFun.assert_has_calls(self.dev_calls, any_order=True)
            for call in self.production_calls:
                assert call not in MockPurgeFun.call_args_list

class TestProcessAnnouncements(unittest.TestCase):
    """tricky category shenanigains are handled and tested in base, 
    we just need to test key generation for different types of announcements
    """
    announcement_data=[
        ("1204.1234", 1, "new", "math.NA", ""),
        ("1204.1235", 1, "new", "cs.", ""),
        ("1104.1234", 3, "cross", "hep-lat astro-ph.SR", "astro-ph.SR"),
        ("1104.1734", 1, "cross", "math.NA math.SG", "math.SG"),
        ("0904.1234", 3, "rep", "hep-lat astro-ph.SR", ""),
        ("1104.1284", 7, "rep", "hep-lat", ""),
        ("1203.1234", 1, "jref", "cs.GL", ""),
        ("1203.1235", 1, "jref", "eess.AS stat.ME", ""),
        ("1112.1234", 1, "wdr", "cs.GL", ""),
        ("1003.1234", 4, "wdr", "math.SG q-bio.NC", "")
    ]

    new_expected=[
            "abs-1204.1234", "paper-id-1204.1234-current", "paper-id-1204.1234v1",
            "abs-1204.1235", "paper-id-1204.1235-current", "paper-id-1204.1235v1",
    ]

    cross_expected=[
        "abs-1104.1234", "year-astro-ph-2011",
        "list-2011-04-hep-lat","list-2011-hep-lat", 
        "list-2011-04-astro-ph.SR", "list-2011-astro-ph.SR", 
        "list-2011-04-astro-ph", "list-2011-astro-ph",
        "list-2011-04-grp_physics",
        "abs-1104.1734", 
        "list-2011-04-math.NA","list-2011-math.NA",
        "list-2011-04-math","list-2011-math",  
        "list-2011-04-math.SG", "list-2011-math.SG", 
        "list-2011-04-cs.NA","list-2011-cs.NA",
        "list-2011-04-cs","list-2011-cs",  
    ]

    rep_expected=[
        "abs-0904.1234", "paper-id-0904.1234-current", "paper-id-0904.1234v3",
        "abs-1104.1284", "paper-id-1104.1284-current", "paper-id-1104.1284v7",
        "list-2009-04-hep-lat","list-2009-hep-lat",
        "list-2009-04-grp_physics", "list-2011-04-grp_physics",
        "list-2009-04-astro-ph.SR","list-2009-astro-ph.SR",
        "list-2009-04-astro-ph","list-2009-astro-ph",
        "list-2011-04-hep-lat","list-2011-hep-lat"
    ]

    jref_expected=[
        "abs-1203.1234",
        "list-2012-03-cs.GL", "list-2012-cs.GL",
        "list-2012-03-cs", "list-2012-cs",
        "abs-1203.1235",
        "list-2012-03-eess.AS", "list-2012-eess.AS",
        "list-2012-03-eess", "list-2012-eess",
        "list-2012-03-stat.ME", "list-2012-stat.ME",
        "list-2012-03-stat", "list-2012-stat"
    ]

    wdr_expected=[
        "abs-1112.1234", "paper-id-1112.1234v1",
        "list-2011-12-cs.GL", "list-2011-cs.GL",
        "list-2011-12-cs", "list-2011-cs",
        "abs-1003.1234", "paper-id-1003.1234v4",
        "list-2010-03-math.SG", "list-2010-math.SG",
        "list-2010-03-math", "list-2010-math",
        "list-2010-03-q-bio.NC", "list-2010-q-bio.NC",
        "list-2010-03-q-bio", "list-2010-q-bio",
    ]

    #a few extra keys due to not having old category information, they dont actually need to be purged, but will be with current implementation
    unneccessary_expected=["year-math-2011"]

    def test_keys_generated(self):
        result=_process_announcements(self.announcement_data)

        for item in self.new_expected:
            self.assertIn(item, result, "missing a key from new announcements")

        for item in self.cross_expected:
            self.assertIn(item, result, "missing a key from cross announcements")

        for item in self.rep_expected:
            self.assertIn(item, result, "missing a key from replace announcements")

        for item in self.jref_expected:
            self.assertIn(item, result, "missing a key from jref announcements")

        for item in self.wdr_expected:
            self.assertIn(item, result, "missing a key from wdr announcements")

        for item in self.unneccessary_expected:
            self.assertIn(item, result, "missing a key from uneeded announcements")

        self.assertEqual(len(result), len(set(result)),"no duplicate keys")
        expected = self.new_expected + self.cross_expected + self.rep_expected + self.jref_expected + self.wdr_expected + self.unneccessary_expected
        self.assertEqual(sorted(result), sorted(list(set(expected))), "all keys are as expected")
        