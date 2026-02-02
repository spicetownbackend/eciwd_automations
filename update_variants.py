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
    offset = 0
    limit = 100
    all_updated = 0

    while True:
        # Fetching products with pagination
        url = f"{BASE_URL}/products?categories={TARGET_CATEGORY_ID}&limit={limit}&offset={offset}&responseFields=items(id,name)"
        response = requests.get(url, headers=HEADERS)
        
        if response.status_code != 200:
            print(f"❌ API Error {response.status_code}: {response.text}")
            break

        items = response.json().get('items', [])
        if not items:
            break

        print(f"--- Prsing batch (Offset: {offset}) ---")

        for item in items:
            p_id, p_name = item['id'], item['name']
            
            # Get full product details to modify options
            p_url = f"{BASE_URL}/products/{p_id}?responseFields=options"
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
                    
                    # Logic: 3+ indices -> 2, 2 indices -> 1
                    if num_choices >= 3:
                        new_default = 2
                    elif num_choices == 2:
                        new_default = 1
                    else:
                        continue

                    option['required'] = False
                    option['defaultChoice'] = new_default
                    changed = True

            if changed:
                put_res = requests.put(f"{BASE_URL}/products/{p_id}", headers=HEADERS, json={"options": data['options']})
                if put_res.status_code == 200:
                    print(f"   ✅ Updated: {p_name}")
                    all_updated += 1
            
            time.sleep(0.2) # Avoid hitting rate limits

        offset += limit

    print(f"\n--- Process Finished. Total Products Updated: {all_updated} ---")

if __name__ == "__main__":
    update_variants()
