from datetime import date

from domain.entities.objectif import Objectif


def make() -> Objectif:
    return Objectif(
        title="100 pros actifs au 31 décembre",
        quarter="T4 2026",
        metric="pros_actifs",
        target=100,
        start_date=date(2026, 10, 1),
        end_date=date(2026, 12, 31),
        created_by=1,
    )


def test_le_rythme_qu_il_faut_tenir():
    suivi = make().suivi(38, date(2026, 10, 12))
    assert suivi.progress == 0.38
    assert suivi.weeks_left == 12  # 80 jours restants, arrondis à la semaine supérieure
    assert suivi.needed_per_week == 5.4  # 62 / (80 / 7)


def test_objectif_atteint():
    suivi = make().suivi(104, date(2026, 12, 1))
    assert suivi.progress == 1.04 and suivi.needed_per_week == 0.0


def test_sans_chiffre_en_direct():
    suivi = make().suivi(None, date(2026, 10, 12))
    assert suivi.current is None and suivi.progress is None and suivi.weeks_left == 12


def test_apres_la_fin():
    suivi = make().suivi(80, date(2027, 1, 15))
    assert suivi.weeks_left == 0 and suivi.needed_per_week == 20.0
