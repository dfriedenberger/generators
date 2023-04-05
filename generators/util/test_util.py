
def test_split():
    from .util import split
    assert ["abc","def","ghi"] == split("AbcDefGhi")
    assert ["abc","def","ghi"] == split("abc_def_ghi")
    assert ["abc","def","ghi"] == split("abcDefGhi")
    assert ["abc","def","ghi"] == split("abc-def-ghi")
    assert ["abc","def","ghi"] == split("Abc Def Ghi")


def test_split():
    from .util import snake_case
    assert "abc_def_ghi" == snake_case("AbcDefGhi")
    assert "abc_def_ghi" == snake_case("abc_def_ghi")
    assert "abc_def_ghi" == snake_case("abcDefGhi")
    assert "abc_def_ghi" == snake_case("abc-def-ghi")
    assert "abc_def_ghi" == snake_case("Abc Def Ghi")

