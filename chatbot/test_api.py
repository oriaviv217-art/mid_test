"""בדיקה ידנית של ה-API. להרצה כשהשרת רץ."""
import requests

BASE = "http://127.0.0.1:5001"

print("-- search 'rotem' --")
print(requests.get(f"{BASE}/api/customers/search", params={"name": "רותם"}).json())

print("\n-- verify: correct id --")
print(requests.post(f"{BASE}/api/customers/verify",
                    json={"customer_id": 22, "national_id": "123456789"}).json())

print("\n-- verify: wrong id --")
print(requests.post(f"{BASE}/api/customers/verify",
                    json={"customer_id": 22, "national_id": "999999999"}).json())

print("\n-- verify: with dashes --")
print(requests.post(f"{BASE}/api/customers/verify",
                    json={"customer_id": 22, "national_id": "123-456-789"}).json())
                    