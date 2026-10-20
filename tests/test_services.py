"""Unit tests for the base62 service."""

import pytest

from app.services import BASE62_ALPHABET, decode_base62, encode_base62, generate_random_code


def test_encode_zero():
    assert encode_base62(0) == "0"


@pytest.mark.parametrize("value", [1, 9, 10, 35, 36, 61, 62, 12345, 987654321])
def test_base62_round_trip(value):
    assert decode_base62(encode_base62(value)) == value


def test_encode_rejects_negative():
    with pytest.raises(ValueError):
        encode_base62(-1)


def test_generated_code_length_and_alphabet():
    code = generate_random_code()
    assert len(code) == 6
    assert all(char in BASE62_ALPHABET for char in code)
    assert len(generate_random_code(10)) == 10
