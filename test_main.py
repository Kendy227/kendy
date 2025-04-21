import os
import time
import hashlib
import requests
import unittest


# Access environment variables
SMILE_EMAIL = "renedysanasam13@gmail.com"
SMILE_UID = "913332"
SMILE_KEY = "84d312c4e0799bac1d363c87be2e14b7"
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
ADMIN_ID = os.getenv("ADMIN_ID")
UPI_ID = os.getenv("UPI_ID")

# API URL
PRODUCT_API_URL = "https://www.smile.one/smilecoin/api/product"
# API URL for product list
PRODUCT_LIST_API_URL = "https://www.smile.one/smilecoin/api/productlist"
# API URL for server list
SERVER_LIST_API_URL = "https://www.smile.one/smilecoin/api/getserver"
# API URL for role query
ROLE_QUERY_API_URL = "https://www.smile.one/smilecoin/api/getrole"
# API URL for purchase
CREATE_ORDER_API_URL = "https://www.smile.one/smilecoin/api/createorder"

# Function to generate the 'sign' parameter
def generate_sign(params, key):
    """
    Generate the 'sign' parameter by sorting fields, concatenating them, appending the key,
    and applying double MD5 hashing.

    :param params: Dictionary of parameters to be signed
    :param key: The encryption key (SMILE_KEY)
    :return: The generated 'sign' parameter
    """
    # Sort the parameters by key
    sorted_params = sorted(params.items())
    # Create a query string from the sorted parameters
    query_string = "&".join(f"{k}={v}" for k, v in sorted_params)
    # Append the key to the query string
    string_to_sign = f"{query_string}&{key}"
    print("String to Sign:", string_to_sign)  # Debugging: Print the string to be signed
    # Apply double MD5 hashing
    return hashlib.md5(hashlib.md5(string_to_sign.encode()).hexdigest().encode()).hexdigest()

# Prepare request parameters
product = "mobilelegends"
request_time = int(time.time())  # Generate the current timestamp

# Parameters to be signed
params = {
    "uid": "913332",
    "email": "renedysanasam13@gmail.com",
    "product": "mobilelegends",
    "time": 1744825223,
}

# Generate the 'sign' parameter
sign = generate_sign(params, SMILE_KEY)

# Add the 'sign' to the payload
payload = {**params, "sign": sign}

# Debugging: Print the payload and sign
print("Payload:", payload)
print("Generated Sign:", sign)

# Send POST request to the product API
response = requests.post(PRODUCT_API_URL, data=payload)

# Handle response
if response.status_code == 200:
    print("Product API Response:", response.json())
else:
    print("Error:", response.status_code, response.text)

# Prepare request parameters
request_time = int(time.time())  # Generate the current timestamp
params = {
    "uid": SMILE_UID,
    "email": SMILE_EMAIL,
    "product": product,
    "time": request_time,
}
sign = generate_sign(params, SMILE_KEY)

payload = {
    "uid": SMILE_UID,
    "email": SMILE_EMAIL,
    "product": product,
    "time": request_time,
    "sign": sign,
}

print("Request URL:", PRODUCT_LIST_API_URL)
print("Payload:", payload)
print("Generated Sign:", sign)

# Send POST request to the product list API
response = requests.post(PRODUCT_LIST_API_URL, data=payload)

# Handle response
if response.status_code == 200:
    print("Product List API Response:", response.json())
else:
    print("Error:", response.status_code, response.text)

# Prepare request parameters
product = "ragnarokm"  # Example product name
request_time = int(time.time())  # Generate the current timestamp
params = {
    "email": SMILE_EMAIL,
    "uid": SMILE_UID,
    "product": product,
    "time": request_time,
}
sign = generate_sign(params, SMILE_KEY)

payload = {
    "email": SMILE_EMAIL,
    "uid": SMILE_UID,
    "product": product,
    "time": request_time,
    "sign": sign,
}

print("Request URL:", SERVER_LIST_API_URL)
print("Payload:", payload)
print("Generated Sign:", sign)

# Send POST request to the server list API
headers = {"Content-Type": "application/x-www-form-urlencoded"}
response = requests.post(SERVER_LIST_API_URL, data=payload, headers=headers)

# Handle response
if response.status_code == 200:
    print("Server List API Response:", response.json())
else:
    print("Error:", response.status_code, response.text)

# Prepare request parameters for Role Query API
userid = "17366"  # Valid user ID
zoneid = "22001"  # Valid zone ID
product = "mobilelegends"  # Example product name
productid = "22590"  # Valid product ID from the Product List API response
request_time = int(time.time())  # Generate the current timestamp

params = {
    "email": SMILE_EMAIL,
    "uid": SMILE_UID,
    "userid": userid,
    "zoneid": zoneid,
    "product": product,
    "productid": productid,
    "time": request_time,
}
sign = generate_sign(params, SMILE_KEY)

payload = {**params, "sign": sign}

print("Request URL:", ROLE_QUERY_API_URL)
print("Payload:", payload)
print("Generated Sign:", sign)

# Send POST request to the Role Query API
response = requests.post(ROLE_QUERY_API_URL, data=payload)

# Handle response
if response.status_code == 200:
    print("Role Query API Response:", response.json())
else:
    print("Error:", response.status_code, response.text)

# Prepare request parameters for Purchase API
userid = "17366"  # Valid user ID
zoneid = "22001"  # Valid zone ID
product = "mobilelegends"  # Example product name
productid = "22590"  # Valid product ID from the Product List API response
request_time = int(time.time())  # Generate the current timestamp

params = {
    "email": SMILE_EMAIL,
    "uid": SMILE_UID,
    "userid": userid,
    "zoneid": zoneid,
    "product": product,
    "productid": productid,
    "time": request_time,
}
sign = generate_sign(params, SMILE_KEY)

payload = {**params, "sign": sign}

print("Request URL:", CREATE_ORDER_API_URL)
print("Payload:", payload)
print("Generated Sign:", sign)

# Send POST request to the Purchase API
response = requests.post(CREATE_ORDER_API_URL, data=payload)

# Handle response
if response.status_code == 200:
    print("Purchase API Response:", response.json())
else:
    print("Error:", response.status_code, response.text)

# Prepare request parameters
userid = "17366"  # Valid user ID
zoneid = "22001"  # Valid zone ID
product = "mobilelegends"  # Example product name
productid = "22590"  # Valid product ID from the Product List API response
request_time = int(time.time())  # Generate the current timestamp
params = {
    "email": SMILE_EMAIL,
    "uid": SMILE_UID,
    "userid": userid,
    "zoneid": zoneid,
    "product": product,
    "productid": productid,
    "time": request_time,
}
sign = generate_sign(params, SMILE_KEY)

payload = {
    "email": SMILE_EMAIL,
    "uid": SMILE_UID,
    "userid": userid,
    "zoneid": zoneid,
    "product": product,
    "productid": productid,
    "time": request_time,
    "sign": sign,
}

print("Request URL:", CREATE_ORDER_API_URL)
print("Payload:", payload)
print("Generated Sign:", sign)

# Send POST request to the purchase API
headers = {"Content-Type": "application/x-www-form-urlencoded"}
response = requests.post(CREATE_ORDER_API_URL, data=payload, headers=headers)

# Handle response
if response.status_code == 200:
    print("Purchase API Response:", response.json())
else:
    print("Error:", response.status_code, response.text)

class TestSmileOneAPI(unittest.TestCase):

    def test_generate_sign(self):
        params = {
            "uid": "913332",
            "email": "renedysanasam13@gmail.com",
            "product": "mobilelegends",
            "time": 1744825223,
        }
        key = "84d312c4e0799bac1d363c87be2e14b7"
        expected_sign = "cc027bb14f8d0a4cdc60ca149a324290"  # Replace with the correct expected value
        generated_sign = generate_sign(params, key)
        self.assertEqual(generated_sign, expected_sign)

if __name__ == "__main__":
    unittest.main()