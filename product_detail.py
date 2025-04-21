import base64
import requests

# Replace with your actual Partner ID and Secret Key
partner_id = "d2c1ab6c0b58488fbd1ee0d7de0511e9"
secret_key = "ha61HJLMhO"

# Generate the Basic Auth value
auth_string = f"{partner_id}:{secret_key}"
auth_bytes = auth_string.encode("utf-8")
auth_base64 = base64.b64encode(auth_bytes).decode("utf-8")

def get_product_detail(product_id):
    # API endpoint for retrieving product details
    api_url = f"https://moogold.com/wp-json/v1/api/product/detail/{product_id}"  # Replace with the actual API endpoint

    # Set up the headers
    headers = {
        "Authorization": f"Basic {auth_base64}"
    }

    # Send the GET request
    response = requests.get(api_url, headers=headers)

    # Check the response status
    if response.status_code == 200:
        print("Product Details Retrieved Successfully:")
        print(response.json())
    else:
        print(f"Failed to retrieve product details. Status Code: {response.status_code}")
        print(f"Response: {response.text}")

# Example usage
product_id = 123  # Replace with the actual product ID
get_product_detail(product_id)