from app.services.ranking import parse_query, rank
from app.services.wmo import compass, describe
from tests.conftest import PARIS


def test_parse_query():
    assert parse_query("Patna, Bihar, India") == ("Patna", ["Bihar", "India"])
    assert parse_query("  Patna  ") == ("Patna", [])
    assert parse_query(" , ") == ("", [])


def test_rank_filters_to_full_context_match():
    out = rank(PARIS["results"], "Paris", ["Texas"])
    assert [r["admin1"] for r in out] == ["Texas"]


def test_rank_prefix_context_match():
    out = rank(PARIS["results"], "Paris", ["Tenn"])
    assert [r["admin1"] for r in out] == ["Tennessee"]


def test_rank_country_code_and_name():
    assert [r["admin1"] for r in rank(PARIS["results"], "Paris", ["FR"])] == ["Île-de-France"]
    assert len(rank(PARIS["results"], "Paris", ["United"])) == 2


def test_rank_falls_back_to_population_when_no_context_matches():
    out = rank(PARIS["results"], "Paris", ["Narnia"])
    assert [r["admin1"] for r in out] == ["Île-de-France", "Texas", "Tennessee"]


def test_rank_without_context_orders_by_population():
    assert rank(PARIS["results"], "Paris", [])[0]["admin1"] == "Île-de-France"


def test_wmo_and_compass():
    assert describe(0, True) == ("Clear sky", "☀️")
    assert describe(0, False)[1] == "🌙"
    assert describe(12345)[0] == "Unknown conditions"
    assert [compass(d) for d in (0, 90, 180, 270, 359)] == ["N", "E", "S", "W", "N"]
