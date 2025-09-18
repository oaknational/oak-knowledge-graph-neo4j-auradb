#!/usr/bin/env python3
"""
Test script to verify HasuraExtractor can connect to real Hasura API
"""
import os
import sys
from pipeline.extractors import HasuraExtractor
from models.config import PipelineConfig

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
    print("✅ Loaded .env file")
except ImportError:
    print("⚠️  python-dotenv not installed, using system environment variables")
    print("   Install with: pip install python-dotenv")


def test_hasura_connection():
    print("Testing Hasura connection...")

    # Check environment variables
    hasura_endpoint = os.getenv("HASURA_ENDPOINT")
    hasura_api_key = os.getenv("HASURA_API_KEY")
    oak_auth_type = os.getenv("OAK_AUTH_TYPE")

    if not hasura_endpoint:
        print("❌ HASURA_ENDPOINT environment variable not set")
        print("   Set it with: export HASURA_ENDPOINT='https://your-hasura-instance.com/v1/graphql'")
        return False

    if not hasura_api_key:
        print("❌ HASURA_API_KEY environment variable not set")
        print("   Set it with: export HASURA_API_KEY='your-oak-auth-key'")
        return False

    if not oak_auth_type:
        print("⚠️  OAK_AUTH_TYPE environment variable not set")
        print("   This might be needed for Oak authentication")
        print("   Set it with: export OAK_AUTH_TYPE='your-oak-auth-type'")

    print(f"✅ Environment variables set")
    print(f"   Endpoint: {hasura_endpoint}")
    print(f"   API Key: {hasura_api_key[:8]}...")

    # Test 1: Initialize extractor
    try:
        extractor = HasuraExtractor()
        print("✅ HasuraExtractor initialized successfully")
    except Exception as e:
        print(f"❌ Failed to initialize HasuraExtractor: {e}")
        return False

    # Test 2: Test connection with a simple introspection query
    print("\nTesting API connection with introspection query...")

    try:
        import requests
        # Try both possible auth header formats
        headers = {
            "Content-Type": "application/json",
            "x-hasura-admin-secret": hasura_api_key,
        }

        # Some Hasura instances use the older header name
        alt_headers = {
            "Content-Type": "application/json",
            "x-hasura-access-key": hasura_api_key,
        }

        # JWT Bearer token (common for 128-char tokens)
        jwt_headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {hasura_api_key}",
        }

        # Oak-specific authentication headers (from TypeScript code)
        oak_headers = {
            "Content-Type": "application/json",
            "x-oak-auth-key": hasura_api_key,
        }

        if oak_auth_type:
            oak_headers["x-oak-auth-type"] = oak_auth_type

        # Simple introspection query to test connection
        introspection_query = """
        query {
          __schema {
            queryType {
              name
            }
          }
        }
        """

        # Alternative simple query (if introspection is blocked)
        simple_query = """
        query {
          __type(name: "Query") {
            name
          }
        }
        """

        # Try primary auth header first
        response = requests.post(
            hasura_endpoint,
            json={"query": introspection_query},
            headers=headers
        )

        if response.status_code == 200:
            result = response.json()
            if "errors" in result and result["errors"]:
                print(f"❌ x-hasura-admin-secret failed: {result['errors'][0]['message']}")
                print("   Trying x-hasura-access-key...")

                # Try alternative header
                response = requests.post(
                    hasura_endpoint,
                    json={"query": introspection_query},
                    headers=alt_headers
                )

                if response.status_code == 200:
                    result = response.json()
                    if "errors" in result and result["errors"]:
                        print(f"❌ x-hasura-access-key also failed: {result['errors'][0]['message']}")
                        print("   Trying JWT Bearer token...")

                        # Try JWT Bearer token
                        response = requests.post(
                            hasura_endpoint,
                            json={"query": introspection_query},
                            headers=jwt_headers
                        )

                        if response.status_code == 200:
                            result = response.json()
                            if "errors" in result and result["errors"]:
                                print(f"❌ JWT Bearer token also failed: {result['errors'][0]['message']}")
                                print("\n🔍 Debug info:")
                                print(f"   Endpoint: {hasura_endpoint}")
                                print(f"   API key length: {len(hasura_api_key)} chars")
                                print(f"   API key starts: {hasura_api_key[:4]}...")
                                print("\n💡 Possible solutions:")
                                print("   1. Check if you need the admin secret instead of JWT")
                                print("   2. Verify the JWT token is valid and not expired")
                                print("   3. Check if additional JWT claims are required")
                                print("   Trying Oak authentication headers...")

                                # Try Oak auth headers
                                response = requests.post(
                                    hasura_endpoint,
                                    json={"query": introspection_query},
                                    headers=oak_headers
                                )

                                if response.status_code == 200:
                                    result = response.json()
                                    if "errors" in result and result["errors"]:
                                        print(f"❌ Oak auth also failed: {result['errors'][0]['message']}")
                                        print("\n⚠️  All auth methods failed, but continuing to test data access...")
                                        headers = oak_headers  # Try Oak for data queries anyway
                                    else:
                                        print("✅ API connection successful with Oak authentication!")
                                        headers = oak_headers  # Use this for subsequent requests
                                else:
                                    print(f"❌ HTTP error with Oak headers: {response.status_code}")
                                    print("\n⚠️  All auth methods failed, but continuing to test data access...")
                                    headers = oak_headers  # Try Oak for data queries anyway
                            else:
                                print("✅ API connection successful with JWT Bearer token!")
                                headers = jwt_headers  # Use this for subsequent requests
                        else:
                            print(f"❌ HTTP error with JWT headers: {response.status_code}")
                            print(f"   Response: {response.text}")
                            return False
                    else:
                        print("✅ API connection successful with x-hasura-access-key!")
                        headers = alt_headers  # Use this for subsequent requests
                else:
                    print(f"❌ HTTP error with alt headers: {response.status_code}")
                    return False
            else:
                print("✅ API connection successful with x-hasura-admin-secret!")
                print(f"   Query type: {result.get('data', {}).get('__schema', {}).get('queryType', {}).get('name', 'unknown')}")
        else:
            print(f"❌ HTTP error: {response.status_code}")
            print(f"   Response: {response.text}")
            return False

    except Exception as e:
        print(f"❌ Connection test failed: {e}")
        return False

    # Test 3: Query actual materialized views
    print("\nTesting access to known materialized views...")

    mv_names = [
        "published_mv_lesson_content_published_9_0_0",
        "published_mv_synthetic_unitvariant_lessons_by_keystage_18_0_0",
        "published_mv_synthetic_unitvariants_with_lesson_ids_by_keystage_18_0_0",
        "published_mv_search_page_10_0_0",
        "published_mv_key_stages_2_0_0",
        "published_mv_curriculum_sequence_b_13_0_20"
    ]

    successful_mvs = []

    for mv_name in mv_names:
        try:
            # Test with limit 1 to just check access
            mv_query = f"""
            query {{
              {mv_name}(limit: 1) {{
                __typename
              }}
            }}
            """

            response = requests.post(
                hasura_endpoint,
                json={"query": mv_query},
                headers=headers
            )

            if response.status_code == 200:
                result = response.json()
                if "errors" in result and result["errors"]:
                    print(f"❌ {mv_name}: {result['errors'][0]['message']}")
                else:
                    row_count = len(result.get("data", {}).get(mv_name, []))
                    print(f"✅ {mv_name}: Accessible (sampled {row_count} row)")
                    successful_mvs.append(mv_name)
            else:
                print(f"❌ {mv_name}: HTTP {response.status_code}")

        except Exception as e:
            print(f"❌ {mv_name}: Error - {e}")

    if successful_mvs:
        print(f"\n🎉 Successfully accessed {len(successful_mvs)}/{len(mv_names)} materialized views!")
        print("\nAccessible materialized views:")
        for mv in successful_mvs:
            print(f"   - {mv}")
    else:
        print("\n❌ Could not access any materialized views")
        return False

    print("\n🎉 Hasura connection test completed successfully!")
    print("\nNext steps:")
    print("1. Choose materialized views from the list above")
    print("2. Test HasuraExtractor with: python3 test_hasura_extraction.py <view_name>")

    return True


if __name__ == "__main__":
    success = test_hasura_connection()
    sys.exit(0 if success else 1)