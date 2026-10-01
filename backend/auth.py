import sqlite3
import secrets
import hashlib
import hmac

from pathlib import Path

from fastapi import (
    APIRouter,
    Request,
    HTTPException
)

from pydantic import BaseModel


# =========================================================
# DATABASE
# =========================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent

DATABASE_DIR = PROJECT_ROOT / "database"

DATABASE_DIR.mkdir(
    parents=True,
    exist_ok=True
)

DATABASE_PATH = DATABASE_DIR / "auth.db"


# =========================================================
# ROUTER
# =========================================================

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"]
)


# =========================================================
# DATABASE CONNECTION
# =========================================================

def get_connection():

    connection = sqlite3.connect(
        DATABASE_PATH
    )

    connection.row_factory = sqlite3.Row

    return connection


# =========================================================
# CREATE USERS TABLE
# =========================================================

def initialize_database():

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS users (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            hospital_name TEXT NOT NULL,

            admin_name TEXT NOT NULL,

            email TEXT UNIQUE NOT NULL,

            password_hash TEXT NOT NULL,

            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP

        )
        """
    )

    connection.commit()

    connection.close()


initialize_database()


# =========================================================
# PASSWORD HASHING
# =========================================================

def hash_password(password: str):

    salt = secrets.token_bytes(32)

    password_hash = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        310000
    )

    return (
        salt.hex()
        + ":"
        + password_hash.hex()
    )


def verify_password(
    password: str,
    stored_password: str
):

    try:

        salt_hex, hash_hex = (
            stored_password.split(":")
        )

        salt = bytes.fromhex(
            salt_hex
        )

        expected_hash = bytes.fromhex(
            hash_hex
        )

        actual_hash = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            salt,
            310000
        )

        return hmac.compare_digest(
            actual_hash,
            expected_hash
        )

    except Exception:

        return False


# =========================================================
# REQUEST MODELS
# =========================================================

class RegisterRequest(BaseModel):

    hospital_name: str

    admin_name: str

    email: str

    password: str


class LoginRequest(BaseModel):

    email: str

    password: str


# =========================================================
# REGISTER USER
# =========================================================

@router.post("/register")
def register_user(
    request: RegisterRequest
):

    hospital_name = (
        request.hospital_name.strip()
    )

    admin_name = (
        request.admin_name.strip()
    )

    email = (
        request.email.strip().lower()
    )

    password = request.password


    # =====================================================
    # BASIC VALIDATION
    # =====================================================

    if not hospital_name:

        raise HTTPException(
            status_code=400,
            detail="Hospital name is required."
        )


    if not admin_name:

        raise HTTPException(
            status_code=400,
            detail="Admin name is required."
        )


    if not email:

        raise HTTPException(
            status_code=400,
            detail="Email is required."
        )


    # =====================================================
    # PASSWORD: MINIMUM 8 CHARACTERS
    # =====================================================

    if len(password) < 8:

        raise HTTPException(
            status_code=400,
            detail=(
                "Password must contain "
                "at least 8 characters."
            )
        )


    # =====================================================
    # PASSWORD: AT LEAST 2 NUMBERS
    # =====================================================

    number_count = sum(
        character.isdigit()
        for character in password
    )


    if number_count < 2:

        raise HTTPException(
            status_code=400,
            detail=(
                "Password must contain "
                "at least 2 numbers."
            )
        )


    # =====================================================
    # PASSWORD: AT LEAST 1 SPECIAL CHARACTER
    # =====================================================

    special_character_exists = any(
        not character.isalnum()
        for character in password
    )


    if not special_character_exists:

        raise HTTPException(
            status_code=400,
            detail=(
                "Password must contain "
                "at least 1 special character."
            )
        )


    # =====================================================
    # CHECK EXISTING USER
    # =====================================================

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT id
        FROM users
        WHERE email = ?
        """,
        (email,)
    )

    existing_user = cursor.fetchone()


    if existing_user:

        connection.close()

        raise HTTPException(
            status_code=409,
            detail=(
                "An account with this email "
                "already exists."
            )
        )


    # =====================================================
    # CREATE USER
    # =====================================================

    password_hash = hash_password(
        password
    )


    cursor.execute(
        """
        INSERT INTO users
        (
            hospital_name,
            admin_name,
            email,
            password_hash
        )
        VALUES (?, ?, ?, ?)
        """,
        (
            hospital_name,
            admin_name,
            email,
            password_hash
        )
    )


    connection.commit()

    user_id = cursor.lastrowid

    connection.close()


    return {

        "status": "success",

        "message":
            "Account created successfully.",

        "user_id":
            user_id

    }


# =========================================================
# LOGIN
# =========================================================

@router.post("/login")
def login_user(
    request: LoginRequest,
    http_request: Request
):

    email = (
        request.email.strip().lower()
    )

    password = request.password


    # =====================================================
    # FIND USER
    # =====================================================

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT
            id,
            hospital_name,
            admin_name,
            email,
            password_hash
        FROM users
        WHERE email = ?
        """,
        (email,)
    )

    user = cursor.fetchone()

    connection.close()


    # =====================================================
    # USER NOT FOUND
    # =====================================================

    if not user:

        raise HTTPException(
            status_code=401,
            detail="Invalid email or password."
        )


    # =====================================================
    # VERIFY PASSWORD
    # =====================================================

    if not verify_password(
        password,
        user["password_hash"]
    ):

        raise HTTPException(
            status_code=401,
            detail="Invalid email or password."
        )


    # =====================================================
    # CREATE SESSION
    # =====================================================

    http_request.session.clear()

    http_request.session["user_id"] = (
        user["id"]
    )


    # =====================================================
    # RESPONSE
    # =====================================================

    return {

        "status": "success",

        "message":
            "Login successful.",

        "user": {

            "id":
                user["id"],

            "hospital_name":
                user["hospital_name"],

            "admin_name":
                user["admin_name"],

            "email":
                user["email"]

        }

    }


# =========================================================
# CURRENT USER
# =========================================================

@router.get("/me")
def current_user(
    request: Request
):

    user_id = (
        request.session.get(
            "user_id"
        )
    )


    if user_id is None:

        raise HTTPException(
            status_code=401,
            detail="Not authenticated."
        )


    connection = get_connection()
    try:
        user = connection.execute(
            """
            SELECT id, hospital_name, admin_name, email
            FROM users
            WHERE id = ?
            """,
            (user_id,),
        ).fetchone()
    finally:
        connection.close()

    if not user:
        request.session.clear()
        raise HTTPException(
            status_code=401,
            detail="Not authenticated.",
        )

    return {

        "status": "success",

        "authenticated": True,

        "user": {

            "id":
                user["id"],

            "hospital_name":
                user["hospital_name"],

            "admin_name":
                user["admin_name"],

            "email":
                user["email"]

        }

    }


# =========================================================
# LOGOUT
# =========================================================

@router.post("/logout")
def logout_user(
    request: Request
):

    request.session.clear()


    return {

        "status": "success",

        "message":
            "Logged out successfully."

    }


# =========================================================
# AUTHORIZATION DEPENDENCY
# =========================================================

def require_auth(
    request: Request
):

    user_id = (
        request.session.get(
            "user_id"
        )
    )


    if not user_id:

        raise HTTPException(
            status_code=401,
            detail="Authentication required."
        )


    return user_id
