import requests
from requests.auth import HTTPBasicAuth
import json

# API Credentials
CLIENT_ID = "AMLRFC"
CLIENT_SECRET = "N6@ko}>49ki6=tUYoZprlKQ[v7-43K+cDf/\\yzhg"
SCOPE = "ZPAYMENT_API_SRV_0001"
STATE = "12345"

# API URL
BASE_URL = "https://s4hana1.amitmetaliks.com:1043"
ENDPOINT = "/sap/opu/odata/sap/ZPAYMENT_API_SRV/ZES_PaymentSet"

def get_oauth_token():
    """Step 1: Get OAuth2 token"""
    token_url = f"{BASE_URL}/sap/bc/sec/oauth2/token"
    
    payload = {
        "grant_type": "client_credentials",
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "scope": SCOPE,
        "state": STATE
    }
    
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    
    response = requests.post(token_url, data=payload, headers=headers, verify=False)
    response.raise_for_status()
    return response.json().get("access_token")


def get_payment_data(token=None):
    """Step 2: Fetch payment data"""
    url = f"{BASE_URL}{ENDPOINT}"
    params = {"$format": "json"}
    
    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    
    response = requests.get(
        url,
        params=params,
        headers=headers,
        verify=False  # Set True if SSL cert is valid
    )
    response.raise_for_status()
    return response.json()


def main():
    print("Fetching Payment API data...\n")
    
    # Try OAuth first
    try:
        print("Attempting OAuth2 token fetch...")
        token = get_oauth_token()
        print(f"Token obtained: {token[:20]}...")
        data = get_payment_data(token=token)
    except Exception as e:
        print(f"OAuth failed: {e}")
        print("Trying Basic Auth fallback...")
        # Fallback: Basic Auth with client_id/secret
        url = f"{BASE_URL}{ENDPOINT}"
        response = requests.get(
            url,
            params={"$format": "json"},
            auth=HTTPBasicAuth(CLIENT_ID, CLIENT_SECRET),
            verify=False
        )
        data = response.json()
    
    # Print results
    print(json.dumps(data, indent=2))
    
    # Extract payment records
    records = data.get("d", {}).get("results", [])
    print(f"\nTotal Payment Records: {len(records)}")
    for rec in records:
        print(rec)


if __name__ == "__main__":
    main()