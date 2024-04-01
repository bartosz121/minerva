import pytest

from minerva.users import schemas


@pytest.mark.parametrize("password", ["Password123!@#", "zaq1@WSX123!@#"])
def test_password_complexity_validator(password: str):
    assert schemas.validate_password_complexity(password)


@pytest.mark.parametrize("password", ["", "abc", "abc123", "password", "password123", "a1A!" * 50])
def test_password_complexity_validator_raises(password: str):
    with pytest.raises(ValueError):
        assert schemas.validate_password_complexity(password)
