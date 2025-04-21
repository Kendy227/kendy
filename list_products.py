import base64
import requests

# Replace with your actual Partner ID and Secret Key
partner_id = "d2c1ab6c0b58488fbd1ee0d7de0511e9"
secret_key = "ha61HJLMhO"

# Generate the Basic Auth value
auth_string = f"{partner_id}:{secret_key}"
auth_bytes = auth_string.encode("utf-8")
auth_base64 = base64.b64encode(auth_bytes).decode("utf-8")

def list_products_by_category(category_id):
    # API endpoint for listing products by category
    api_url = f"https://moogold.com/wp-json/v1/api/product/list/{category_id}"  # Replace with the actual API endpoint

    # Set up the headers
    headers = {
        "Authorization": f"Basic {auth_base64}"
    }

    # Send the GET request
    response = requests.get(api_url, headers=headers)

    # Check the response status
    if response.status_code == 200:
        print("Products Retrieved Successfully:")
        print(response.json())
    else:
        print(f"Failed to retrieve products. Status Code: {response.status_code}")
        print(f"Response: {response.text}")

# Example usage
category_id = 50  # Replace with the actual category ID (e.g., 50 for Direct-top up products)
list_products_by_category(category_id)