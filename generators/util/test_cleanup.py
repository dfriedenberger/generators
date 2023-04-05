
def test_remove_duplicates():
    from .cleanup import remove_duplicates

    assert [{"name" : "x"}] == remove_duplicates([{"name" : "x"}])
    assert [{"name" : "x"}] == remove_duplicates([{"name" : "x"},{"name" : "x"}])