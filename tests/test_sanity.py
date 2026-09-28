from datetime import timedelta

from kitvending_api import MSK


def test_msk_offset():
    assert MSK.utcoffset(None) == timedelta(hours=3)
