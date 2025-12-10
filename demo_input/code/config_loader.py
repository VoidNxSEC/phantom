#!/usr/bin/env python3
"""Configuration loader with secrets."""

import os

# WARNING: These are dummy credentials for demo
DATABASE_URL = "postgres://admin:password123@db.internal.com:5432/prod"
AWS_ACCESS_KEY = "AKIAIOSFODNN7EXAMPLE"
AWS_SECRET_KEY = "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"
API_ENDPOINT = "https://api.secretservice.com/v2"

def load_config():
    return {
        "db": DATABASE_URL,
        "aws_key": AWS_ACCESS_KEY,
        "email_admin": "admin@internal.corp",
    }
