import os
import requests
import time

# --- Fetch Environment Variables ---
# Ensure these match the 'env' keys in your YAML exactly
API_TOKEN = os.getenv('ECWID_API_TOKEN')
BASE_URL = os.getenv('ECWID_BASE_URL')

TARGET_CATEGORY_ID = 194057007
TARGET_OPTION_NAME = "Variant"

if not API_TOKEN or not BASE_URL:
    print("❌ ERROR: Missing ECWID_API_TOKEN or ECWID_BASE_URL in environment.")
    exit(1)

# FIXED: Defining HEADERS to match the usage below
HEADERS = {
    'Authorization': f'Bearer {API_TOKEN}',
    'Content-Type': 'application/json'
}

def update_variants():
    # 1. Fetch all products in the category
    url = f"{BASE_URL}/products?categories={TARGET_CATEGORY_ID}&responseFields=items(id,name)"
    response = requests.get(url, headers=HEADERS)
    
    if response.status_code != 200:
        print(f"❌ Failed to fetch category: {response.status_code}")
        return

    products = response.json().get('items', [])
    print(f"Found {len(products)} products in category {TARGET_CATEGORY_)

    for item in products:
        p_id, p_name = item['id'], item['name']
        
        # 2. Get specific product options
        p_url = f"{BASE_URL}/products/{p_id}?responseFields=options"
        # FIXED: Changed 'HEADS' to 'HEADERS' to match defined variable
        res = requests.get(p_url, headers=HEADERS)
        
        if res.status_code != 200:
            print(f"   ⚠️ Could not fetch details for {p_name}")
            continue
            
        data = res.json()

        if 'options' not in data:
            continue

        changed = False
        for option in data['options']:
            if option['name'] == TARGET_OPTION_NAME:
                num_choices = len(option.get('choices', []))
                
                # Applying Logic: 3+ indices -> 2, 2 indices -> 1
                if num_choices >= 3:
                    new_default = 2
                elif num_choices == 2:
                    new_default = 1
                else:
                    continue

            option['required'] = False
                option['defaultChoice'] = new_default
                changed = True
                print(f"   ✅ {p_name}: Default set to index {new_default}")

        if changed:
            requests.put(f"{BASE_URL}/products/{p_id}", headers=HEADERS, json={"options": data['options']})
        
        time.sleep(0.2) # API Rate limit safety

if __name__ == "__main__":
    update_variants()
