from datetime import timedelta

from KVApi import MSK


def test_msk_offset():
    assert MSK.utcoffset(None) == timedelta(hours=3)
