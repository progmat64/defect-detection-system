import numpy as np
from defect_detection.features import rle_decode, rle_encode


def test_rle_roundtrip():
    # создай маску 256x1600 с нулями
    mask = np.zeros((256, 1600), dtype=np.uint8)
    # поставь несколько единиц
    mask[10:20, 100:200] = 1
    # закодируй → декодируй → сравни
    encoded = rle_encode(mask)
    decoded = rle_decode(encoded)
    assert np.array_equal(decoded, mask)


def test_rle_empty_mask():
    mask = np.zeros((256, 1600), dtype=np.uint8)
    encoded = rle_encode(mask)
    assert encoded == ""