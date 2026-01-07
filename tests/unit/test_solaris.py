import pytest

from core.solaris import SolarisState, update_solaris_intensity


@pytest.mark.unit
def test_solaris_intensity_clamped():
    solaris = SolarisState()
    update_solaris_intensity(solaris=solaris, tension=2.0, earth_pressure=2.0)
    assert 0.0 <= solaris.intensity <= 1.0
