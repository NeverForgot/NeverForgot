from datetime import datetime, timedelta, timezone

from trakist.timeutils import as_naive_utc, utcnow


def test_as_naive_utc_laisse_un_naive_inchange() -> None:
    naive = datetime(2026, 7, 14, 12, 0, 0)
    assert as_naive_utc(naive) == naive
    assert as_naive_utc(naive).tzinfo is None


def test_as_naive_utc_convertit_un_aware_en_utc_naive() -> None:
    aware_utc = datetime(2026, 7, 14, 12, 0, 0, tzinfo=timezone.utc)
    assert as_naive_utc(aware_utc) == datetime(2026, 7, 14, 12, 0, 0)


def test_as_naive_utc_convertit_un_autre_fuseau_en_utc() -> None:
    plus_deux = timezone(timedelta(hours=2))
    aware = datetime(2026, 7, 14, 14, 0, 0, tzinfo=plus_deux)  # = 12:00 UTC
    assert as_naive_utc(aware) == datetime(2026, 7, 14, 12, 0, 0)


def test_comparaison_coherente_entre_naive_et_aware_representant_le_meme_instant() -> None:
    """Le bug reproduit en conditions reelles : Postgres renvoie des
    datetime aware pour DateTime(timezone=True), SQLite les renvoie naive.
    Sans normalisation, comparer les deux leve TypeError."""
    naive = datetime(2026, 7, 14, 12, 0, 0)
    aware = datetime(2026, 7, 14, 12, 0, 0, tzinfo=timezone.utc)

    assert as_naive_utc(naive) == as_naive_utc(aware)
    assert not (as_naive_utc(naive) < as_naive_utc(aware))


def test_utcnow_renvoie_un_datetime_aware() -> None:
    assert utcnow().tzinfo is not None
