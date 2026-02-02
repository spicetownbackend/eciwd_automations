import os
import requests
import time

# --- Setup from Environment ---
API_TOKEN = os.getenv('ECWID_API_TOKEN')
BASE_URL = os.getenv('ECWID_BASE_URL')
TARGET_CATEGORY_ID = 194057007
TARGET_OPTION_NAME = "Variant"

if not API_TOKEN or not BASE_URL:
    print("❌ ERROR: Missing ECWID_API_TOKEN or ECWID_BASE_URL in environment.")
    exit(1)

HEADERS = {
    'Authorization': f'Bearer {API_TOKEN}',
    'Content-Type': 'application/json'
}

def update_variants():
    # Fetching products in category
    url = f"{BASE_URL}/products?categories={TARGET_CATEGORY_ID}&responseFields=items(id,name)"
    response = requests.get(url, headers=HEADERS)
    
    if response.status_code != 200:
        print(f"❌ API Error: {response.status_code}")
        return

    products = response.json().get('items', [])
    # FIXED: Corrected the f-string syntax error from your screenshot
    print(f"Found {len(products)} products in category {TARGET_CATEGORY_ID}")

    for item in products:
        p_id, p_name = item['id'], item['name']
        
        # Get product options
        p_url = f"{BASE_URL}/products/{p_id}?responseFields=options"
        # FIXED: Changed 'HEADS' to 'HEADERS' to fix the NameError
        res = requests.get(p_url, headers=HEADERS)
        
        if res.status_code != 200:
            continue
            
        data = res.json()
        if 'options' not in data:
            continue

        changed = False
        for option in data['options']:
            if option['name'] == TARGET_OPTION_NAME:
                num_choices = len(option.get('choices', []))
                
                if num_choices >= 3:
                    new_default = 2
                elif num_choices == 2:
                    new_default = 1
                else:
                    continue

                option['required'] = False
                option['defaultChoice'] = new_default
                changed = True
                print(f"   ✅ {p_name}: Set default to index {new_default}")

        if changed:
            requests.put(f"{BASE_URL}/products/{p_id}", headers=HEADERS, json={"options": data['options']})
        
        time.sleep(0.2) 

if __name__ == "__main__":
    update_variants()
