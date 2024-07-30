
import sys, os
sys.path.append( os.path.join(os.path.dirname(__file__), "..", "src") )
from main import process_paper_categories, PaperCategories

def test_process_cats_basic():
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