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
                    
print("\n-- appointments: verified --")
print(requests.post(f"{BASE}/api/customers/appointments",
                    json={"customer_id": 22, "national_id": "123456789"}).json())

print("\n-- appointments: wrong id (must leak nothing) --")
print(requests.post(f"{BASE}/api/customers/appointments",
                    json={"customer_id": 22, "national_id": "000000000"}).json())

print("\n-- appointments: customer with no appointments --")
print(requests.post(f"{BASE}/api/customers/appointments",
                    json={"customer_id": 24, "national_id": "246813579"}).json())