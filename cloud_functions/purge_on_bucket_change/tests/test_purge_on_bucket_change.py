from unittest.mock import Mock
from arxiv.identifier import Identifier

import sys, os
sys.path.append( os.path.join(os.path.dirname(__file__), "..", "src") )
from main import _paperid, invalidate_for_gs_change

def test_paper_id():
    #nonsense text
    path="absolutenonsesnse"
    assert _paperid(path) is None

    #new id
    path="ps_cache/arxiv/html/0712/0712.3116v1/index.html"
    assert _paperid(path) == Identifier("0712.3116v1")

    #old id
    path="ps_cache/cs/pdf/0005/0005003v3.pdf"
    assert _paperid(path) == Identifier("cs/0005003v3")


def test_invalidate_keys():
    mock_invalidator = Mock()

    #basic
    path="ps_cache/arxiv/html/0712/0712.3116v1/index.html"
    invalidate_for_gs_change("bucket", path, mock_invalidator)
    expected=["html-0712.3116v1", "html-0712.3116-current"]
    actual=mock_invalidator.invalidate.call_args[0][0]
    assert sorted(expected)==sorted(actual)
    mock_invalidator.reset_mock()

    #weird html files
    path="ps_cache/arxiv/html/0712/0712.3116v5/fancy.png"
    invalidate_for_gs_change("bucket", path, mock_invalidator)
    expected=["html-0712.3116v5", "html-0712.3116-current"]
    actual=mock_invalidator.invalidate.call_args[0][0]
    assert sorted(expected)==sorted(actual)
    mock_invalidator.reset_mock()

    #pdf path
    path="ps_cache/cs/pdf/0712/0712.3116v2.pdf"
    invalidate_for_gs_change("bucket", path, mock_invalidator)
    expected=["pdf-0712.3116v2", "pdf-0712.3116-current"]
    actual=mock_invalidator.invalidate.call_args[0][0]
    assert sorted(expected)==sorted(actual)
    mock_invalidator.reset_mock()

    #old ids
    path="ps_cache/cs/pdf/0005/0005003v1.pdf"
    invalidate_for_gs_change("bucket", path, mock_invalidator)
    expected=["pdf-cs/0005003v1", "pdf-cs/0005003-current"]
    actual=mock_invalidator.invalidate.call_args[0][0]
    assert sorted(expected)==sorted(actual)
    mock_invalidator.reset_mock()
    