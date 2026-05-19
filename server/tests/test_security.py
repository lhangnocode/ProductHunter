from app.core.security import verify_password, get_password_hash, create_access_token, create_refresh_token
from jose import jwt
from app.core.config import settings

def test_password_hashing():
    password = "secretpassword123"
    hashed = get_password_hash(password)
    
    assert hashed != password
    assert verify_password(password, hashed) is True
    assert verify_password("wrongpassword", hashed) is False

def test_create_access_token():
    data = {"sub": "testuser"}
    token = create_access_token(data)
    
    decoded = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    assert decoded["sub"] == "testuser"
    assert "exp" in decoded

def test_create_refresh_token():
    data = {"sub": "testuser"}
    token = create_refresh_token(data)
    
    decoded = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    assert decoded["sub"] == "testuser"
    assert decoded["type"] == "refresh"
    assert "exp" in decoded
