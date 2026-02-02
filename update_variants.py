import os
import requests
import time

# --- Fetch Environment Variables ---
API_TOKEN = os.getenv('ECWID_API_TOKEN')
BASE_URL = os.getenv('ECWID_BASE_URL')
TARGET_CATEGORY_ID = 194057007
TARGET_OPTION_NAME = "Variant"

if not API_TOKEN or not BASE_URL:
    print("❌ ERROR: Missing API_TOKEN or BASE_URL in environment.")
    exit(1)

HEADERS = {
    'Authorization': f'Bearer {API_TOKEN}',
    'Content-Type': 'application/json'
}

def update_variants():
    # 1. Fetch all products in the category
    url = f"{BASE_URL}/products?categories={TARGET_CATEGORY_ID}&responseFields=items(id,name)"
    response = requests.get(url, headers=HEADERS)
    products = response.json().get('items', [])

    print(f"Found {len(products)} products in category {TARGET_CATEGORY_ID}")

    for item in products:
        p_id, p_name = item['id'], item['name']
        
        # 2. Get specific product options
        p_url = f"{BASE_URL}/products/{p_id}?responseFields=options"
        data = requests.get(p_url, headers=HEADS).json()

        if 'options' not in data:
            continue

        changed = False
        for option in data['options']:
            if option['name'] == TARGET_OPTION_NAME:
                num_choices = len(option.get('choices', []))
                
                # YOUR LOGIC RULES
                if num_choices >= 3:
                    new_default = 2
                elif num_choices == 2:
                    new_default = 1
                else:
                    continue

                option['required'] = False
                option['defaultChoice'] = new_default
                changed = True
                print(f"   ✅ {p_name}: Set default to {new_default}")

        if changed:
            requests.put(f"{BASE_URL}/products/{p_id}", headers=HEADERS, json={"options": data['options']})
        
        time.sleep(0.2) # API Rate limit safety

if __name__ == "__main__":
    update_variants()
