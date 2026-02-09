import requests
import os
import db_manager as db

# 1. GET CONFIG
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
    Returns: 'active', 'inactive', or 'trial'
    """
    if not LS_API_KEY:
        # Dev safety: If no key, don't lock everyone out, but don't grant full access.
        return "trial"

    try:
        url = "https://api.lemonsqueezy.com/v1/subscriptions"
        params = {
            "filter[user_email]": user_email,
            "filter[store_id]": LS_STORE_ID 
        }
        
        response = requests.get(url, headers=HEADERS, params=params)
        
        if response.status_code == 200:
            data = response.json()
            
            # CASE A: No Record Found -> TRIAL
            if not data['data']:
                return "trial"
            
            # CASE B: Record Found -> Check Status
            # Lemon Squeezy returns a list. We check the most recent one.
            latest_sub = data['data'][0]
            ls_status = latest_sub['attributes']['status']
            
            # MAPPING LEMON SQUEEZY STATUSES TO SIGNET STATUSES
            # LS: on_trial, active, paused, past_due, unpaid, cancelled, expired
            
            if ls_status in ['active', 'on_trial']:
                return "active"
            
            elif ls_status in ['cancelled', 'expired', 'unpaid']:
                return "inactive" # They churned
            
            elif ls_status == 'past_due':
                return "inactive" # Strict: No pay, no play.
                
            else:
                return "trial" # Fallback
                
        else:
            print(f"⚠️ LS API ERROR: {response.status_code}")
            return "trial" 
            
    except Exception as e:
        print(f"⚠️ SUBSCRIPTION CHECK FAILED: {e}")
        return "trial"

def sync_user_status(username, email):
    """
    The Doorman.
    1. Checks if they are a 'Retainer' (Manual Grant).
    2. If not, checks Lemon Squeezy.
    3. Updates DB.
    """
    
    # 1. CHECK LOCAL DB FOR MANUAL OVERRIDES
    # We need to peek at the current status first
    # (We will add a quick check function to db_manager for this)
    current_status = db.get_user_status(username)
    
    # PROTECTED STATUSES: If you manually set them to these, the API won't touch them.
    if current_status in ["retainer", "lifetime", "admin"]:
        return "active"

    # 2. ASK LEMON SQUEEZY
    real_status = check_subscription_status(email)
    
    # 3. UPDATE DB
    db.update_user_status(username, real_status)
    
    return real_status
