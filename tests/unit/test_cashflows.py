from fin_infra.cashflows.core import npv, irr


def test_cashflows_basic():
    cf = [-1000, 200, 300, 400, 500]
    assert isinstance(npv(0.08, cf), float)
    r = irr(cf)
    assert isinstance(r, float)
    assert -1.0 < r < 1.0
