import os
import requests
import time
import smtplib
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# --- CONFIGURATION & SECRETS ---
API_TOKEN = os.getenv('ECWID_API_TOKEN')
BASE_URL = os.getenv('ECWID_BASE_URL')
EMAIL_USER = os.getenv('EMAIL_USER')
EMAIL_PASS = os.getenv('EMAIL_PASS')
EMAIL_CC = os.getenv('EMAIL_CC')

# --- TARGETS ---
TARGET_CATEGORY_ID = 194057007
TARGET_OPTION_NAME = "Variant"

# --- INPUT FIELD CONFIG ---

# 1. DELETE THESE: List of exact names to remove (Case Sensitive)
REMOVE_OPTION_NAMES = ["Message", "Special Instructions", "Special Instructions/Customization Notes"] 

# 2. ADD/ENSURE THIS: The field we want to keep/add
ENSURE_INPUT_FIELD = True
TARGET_INPUT_FIELD = {
    "type": "TEXTAREA",
    "name": "Customization Notes/Special Instructions",
    "required": False,
    "choices": []
}

# CHECK ENV VARS
if not all([API_TOKEN, BASE_URL, EMAIL_USER, EMAIL_PASS]):
    print("❌ ERROR: Missing environment variables.")
    exit(1)

HEADERS = {
    'Authorization': f'Bearer {API_TOKEN}',
    'Content-Type': 'application/json'
}

def send_email_report(stats):
    print("📧 Sending Email Notification...")
    today_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    if stats['errors'] > 0:
        status_tag = "[WARNING]" 
    elif stats['updated'] > 0:
        status_tag = "[SUCCESS]"
    else:
        status_tag = "[NO CHANGES]"

    subject = f"{status_tag} Ecwid Sync Repair: {today_str}"
    
    body = f"""
    <html><body>
        <h2>Ecwid Sync Repair Report</h2>
        <p><b>Run Date:</b> {today_str}</p>
        <p><b>Target Category:</b> {TARGET_CATEGORY_ID}</p>
        <hr>
        <h3>Summary Stats:</h3>
        <ul>
            <li><b>Total Scanned:</b> {stats['scanned']}</li>
            <li><b>Products Updated:</b> {stats['updated']}</li>
            <li><b>Errors:</b> {stats['errors']}</li>
        </ul>
        <hr>
        <p><i>Automated repair for Clover sync overwrites.</i></p>
    </body></html>
    """

    try:
        msg = MIMEMultipart()
        msg['From'] = EMAIL_USER
        msg['To'] = EMAIL_USER 
        msg['Subject'] = subject
        
        recipients = [EMAIL_USER]
        if EMAIL_CC and EMAIL_CC.strip():
            msg['Cc'] = EMAIL_CC
            recipients.append(EMAIL_CC)

        msg.attach(MIMEText(body, 'html'))

        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(EMAIL_USER, EMAIL_PASS)
        server.sendmail(EMAIL_USER, recipients, msg.as_string())
        server.quit()
        print(f"   ✅ Email sent to {recipients}")
        
    except Exception as e:
        print(f"   ❌ [Error] Failed to send email: {e}")

def update_products():
    stats = { 'scanned': 0, 'updated': 0, 'errors': 0 }
    offset = 0
    limit = 100

    print(f"🚀 Starting repair for Category {TARGET_CATEGORY_ID}...")

    while True:
        # 1. Fetch products
        url = f"{BASE_URL}/products?categories={TARGET_CATEGORY_ID}&offset={offset}&limit={limit}&responseFields=items(id,name,options)"
        
        try:
            response = requests.get(url, headers=HEADERS)
            response.raise_for_status()
        except Exception as e:
            print(f"❌ API Error: {e}")
            stats['errors'] += 1
            break

        products = response.json().get('items', [])
        if not products:
            print("✅ End of list reached.")
            break

        print(f"   ... Processing batch {offset} to {offset + len(products)}")

        for item in products:
            stats['scanned'] += 1
            p_id, p_name = item.get('id'), item.get('name')
            options = item.get('options', [])
            
            if options is None: options = []

            changed = False
            
            # --- TASK A: DELETE UNWANTED OPTIONS ---
            # We recreate the list, keeping only options that are NOT in the remove list
            original_count = len(options)
            options = [opt for opt in options if opt['name'] not in REMOVE_OPTION_NAMES]
            
            if len(options) < original_count:
                print(f"      🗑️  {p_name}: Deleted {original_count - len(options)} unwanted option(s).")
                changed = True

            # --- TASK B: FIX VARIANT DEFAULTS ---
            for option in options:
                if option['name'] == TARGET_OPTION_NAME:
                    num_choices = len(option.get('choices', []))
                    current_default = option.get('defaultChoice')
                    new_default = None

                    if num_choices >= 3:
                        new_default = 2
                    elif num_choices == 2:
                        new_default = 1
                    
                    if new_default is not None and current_default != new_default:
                        print(f"      📝 {p_name}: Correcting Default Variant {current_default} -> {new_default}")
                        option['required'] = False
                        option['defaultChoice'] = new_default
                        changed = True

            # --- TASK C: ENSURE TARGET INPUT FIELD ---
            if ENSURE_INPUT_FIELD:
                input_found = False
                for option in options:
                    if option['name'] == TARGET_INPUT_FIELD['name'] and option['type'] == TARGET_INPUT_FIELD['type']:
                        input_found = True
                        break
                
                if not input_found:
                    print(f"      ➕ {p_name}: Adding missing input field '{TARGET_INPUT_FIELD['name']}'")
                    options.append(TARGET_INPUT_FIELD.copy())
                    changed = True

            # --- UPDATE CALL ---
            if changed:
                try:
                    res = requests.put(
                        f"{BASE_URL}/products/{p_id}", 
                        headers=HEADERS, 
                        json={"options": options}
                    )
                    if res.status_code == 200:
                        stats['updated'] += 1
                        time.sleep(0.2) 
                    else:
                        print(f"      ❌ Failed to update {p_name}: {res.status_code}")
                        stats['errors'] += 1
                except Exception as e:
                    print(f"      ❌ Network error on {p_name}: {e}")
                    stats['errors'] += 1

        offset += limit

    print(f"🎉 Job Done. Stats: {stats}")
    send_email_report(stats)

if __name__ == "__main__":
    update_products()
