from arxiv.taxonomy.definitions import CATEGORIES

import sys, os
sys.path.append( os.path.join(os.path.dirname(__file__), "..", "src") )
from main import process_paper_categories, PaperCategories

def test_process_cats_basic():
    "tests basic processing for "
    data=[
        ("1234.5678", "math.GM", 1),
        ("1234.5679", "hep-lat", 1),
        ("1234.5679", "q-fin.CP", 0),
        ("1234.5679", "q-fin.PM", 0)
    ]
    result= process_paper_categories(data)

    expected1=PaperCategories("1234.5678")
    expected1.add_primary("math.GM")
    expected2=PaperCategories("1234.5679")
    expected2.add_primary("hep-lat")
    expected2.add_cross("q-fin.CP")
    expected2.add_cross("q-fin.PM")
    expected={
        "1234.5678":expected1,
        "1234.5679":expected2,
    }
    assert result == expected

def test_paper_categories_basic():
    "tests that paper categories class works as expected"

    #initial creation
    item= PaperCategories("1234.5678")
    assert item.paper_id == "1234.5678"
    assert item.primary is None
    assert item.crosses == set()

    #add a crosslist
    item.add_cross("hep-lat")
    assert item.paper_id == "1234.5678"
    assert item.primary is None
    assert item.crosses == {CATEGORIES["hep-lat"]}

    #add a primary listing
    item.add_primary("physics.ins-det")
    assert item.paper_id == "1234.5678"
    assert item.primary == CATEGORIES["physics.ins-det"]
    assert item.crosses == {CATEGORIES["hep-lat"]}

    #add another crosslist
    item.add_cross("q-bio.PE")
    assert item.paper_id == "1234.5678"
    assert item.primary == CATEGORIES["physics.ins-det"]
    assert item.crosses == {CATEGORIES["hep-lat"], CATEGORIES["q-bio.PE"]}

def test_paper_categories_subsumed():
    """test that only the canonical version of subsumed archives is used 
    duplicates caused by this are avoided"""

    #converts to canon correctly
    item= PaperCategories("1234.5678")
    item.add_cross("chao-dyn")
    assert item.paper_id == "1234.5678"
    assert item.primary is None
    assert item.crosses == {CATEGORIES["nlin.CD"]}

    #doesnt duplicate cross
    item.add_cross("chao-dyn")
    assert item.primary is None
    assert item.crosses == {CATEGORIES["nlin.CD"]}

    #doesn't duplicate even if alt name is used
    item.add_cross("nlin.CD")
    assert item.primary is None
    assert item.crosses == {CATEGORIES["nlin.CD"]}

    #adding as primary uses canonical name and removes duplicate entry in cross
    item.add_primary("chao-dyn")
    assert item.primary == CATEGORIES["nlin.CD"]
    assert item.crosses == set()

    #cant add a matching crosslist
    item.add_cross("nlin.CD")
    assert item.primary == CATEGORIES["nlin.CD"]
    assert item.crosses == set()

    #can add alternately named crosslist
    item.add_cross("chao-dyn")
    assert item.primary == CATEGORIES["nlin.CD"]
    assert item.crosses == set()

def test_paper_categories_alias():
    """test that only the canonical version of alias is used 
    duplicates caused by this are avoided"""

    #converts to canon correctly
    item= PaperCategories("1234.5678")
    item.add_cross("cs.SY")
    assert item.paper_id == "1234.5678"
    assert item.primary is None
    assert item.crosses == {CATEGORIES["eess.SY"]}

    #doesnt duplicate cross
    item.add_cross("cs.SY")
    assert item.primary is None
    assert item.crosses == {CATEGORIES["eess.SY"]}

    #doesn't duplicate even if alt name is used
    item.add_cross("eess.SY")
    assert item.primary is None
    assert item.crosses == {CATEGORIES["eess.SY"]}

    #adding as primary uses canonical name and removes duplicate entry in cross
    item.add_primary("cs.SY")
    assert item.primary == CATEGORIES["eess.SY"]
    assert item.crosses == set()

    #cant add a matching crosslist
    item.add_cross("eess.SY")
    assert item.primary == CATEGORIES["eess.SY"]
    assert item.crosses == set()

    #can add alternately named crosslist
    item.add_cross("cs.SY")
    assert item.primary == CATEGORIES["eess.SY"]
    assert item.crosses == set()