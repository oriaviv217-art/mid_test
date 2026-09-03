import api_client

print(api_client.search_customers("רותם"))
print(api_client.verify(22, "123456789"))
print(api_client.verify(22, "999999999"))
print(api_client.get_appointments(22, "123456789"))