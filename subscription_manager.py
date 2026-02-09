import requests
import os
import db_manager as db

# 1. GET CONFIG FROM RAILWAY
# We use os.environ.get to safely read the key you will add later
LS_API_KEY = os.environ.get("LEMONSQUEEZY_API_KEY")
LS_STORE_ID = os.environ.get("LEMONSQUEEZY_STORE_ID") 

HEADERS = {
    "Accept": "application/vnd.api+json",
    "Content-Type": "application/vnd.api+json",
    "Authorization": f"Bearer {LS_API_KEY}"
}

def check_subscription_status(user_email):
    """
    Pings Lemon Squeezy to see if this email has an active subscription.
    Returns: 'active' or 'trial' (or 'past_due', etc.)
    """
    if not LS_API_KEY:
        print("⚠️ DEBUG: No API Key found. Defaulting to TRIAL mode.")
        return "trial"

    try:
        # 2. QUERY LEMON SQUEEZY
        # We search for subscriptions attached to this email
        url = "https://api.lemonsqueezy.com/v1/subscriptions"
        params = {
            "filter[user_email]": user_email,
            "filter[store_id]": LS_STORE_ID 
        }
        
        response = requests.get(url, headers=HEADERS, params=params)
        
        if response.status_code == 200:
            data = response.json()
            
            # 3. CHECK RESULTS
            # If no data comes back, they never bought anything.
            if not data['data']:
                return "trial"
            
            # If data exists, check the status of the *most recent* subscription
            # (Lemon Squeezy returns a list, usually most recent first)
            latest_sub = data['data'][0]
            status = latest_sub['attributes']['status']
            
            # Map LS status to our DB status
            # LS Statuses: active, past_due, unpaid, cancelled, expired, on_trial
            if status in ['active', 'on_trial']:
                return "active"
            else:
                return "trial" # They bought it but cancelled/expired
                
        else:
            print(f"⚠️ LS API ERROR: {response.status_code} - {response.text}")
            return "trial" # Fail safe: don't give free access on error
            
    except Exception as e:
        print(f"⚠️ SUBSCRIPTION CHECK FAILED: {e}")
        return "trial" # Fail safe

def sync_user_status(username, email):
    """
    The main function called by app.py on login.
    Checks LS, then updates the local database.
    """
    # 1. Ask the Bouncer
    real_status = check_subscription_status(email)
    
    # 2. Update the Database
    # We need to add a quick function to db_manager to update status
    # (We will add that in a second)
    db.update_user_status(username, real_status)
    
    return real_status
