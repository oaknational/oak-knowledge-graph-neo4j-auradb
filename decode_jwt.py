#!/usr/bin/env python3
"""
Decode JWT token to inspect claims (without verification)
"""
import base64
import json
import os
from dotenv import load_dotenv

load_dotenv()

def decode_jwt_payload(token):
    """Decode JWT payload without verification (for debugging only)"""
    try:
        # JWT has 3 parts: header.payload.signature
        parts = token.split('.')
        if len(parts) != 3:
            return None, "Invalid JWT format - should have 3 parts"

        # Decode payload (2nd part)
        payload = parts[1]

        # Add padding if needed
        padding = len(payload) % 4
        if padding:
            payload += '=' * (4 - padding)

        decoded_bytes = base64.urlsafe_b64decode(payload)
        payload_json = json.loads(decoded_bytes)

        return payload_json, None

    except Exception as e:
        return None, f"Error decoding JWT: {e}"

def main():
    token = os.getenv("HASURA_API_KEY")

    if not token:
        print("❌ HASURA_API_KEY not found in environment")
        return

    print(f"🔍 Analyzing JWT token (length: {len(token)} chars)")
    print(f"   Starts with: {token[:10]}...")

    payload, error = decode_jwt_payload(token)

    if error:
        print(f"❌ {error}")
        return

    print("\n📋 JWT Payload:")
    print(json.dumps(payload, indent=2))

    # Check common JWT claims
    print("\n🔑 Key Claims:")

    # Standard claims
    if 'exp' in payload:
        import datetime
        exp_timestamp = payload['exp']
        exp_date = datetime.datetime.fromtimestamp(exp_timestamp)
        now = datetime.datetime.now()

        if exp_date > now:
            print(f"   ✅ Expires: {exp_date} (valid)")
        else:
            print(f"   ❌ Expires: {exp_date} (EXPIRED)")

    if 'iss' in payload:
        print(f"   📍 Issuer: {payload['iss']}")

    if 'aud' in payload:
        print(f"   🎯 Audience: {payload['aud']}")

    # Hasura-specific claims
    hasura_claims = {}
    for key, value in payload.items():
        if 'hasura' in key.lower():
            hasura_claims[key] = value

    if hasura_claims:
        print("\n🏗️  Hasura Claims:")
        for key, value in hasura_claims.items():
            print(f"   {key}: {value}")
    else:
        print("\n⚠️  No Hasura-specific claims found")
        print("   This might explain the authentication failure")

if __name__ == "__main__":
    main()