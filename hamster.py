import requests
import time
import random
from concurrent.futures import ThreadPoolExecutor, as_completed

def generate_client_id():
    
    return f"{random.randint(1000000000000, 9999999999999)}-{random.randint(100000000000000000, 999999999999999999)}"

def run_promo_operations():
    
    login_url = 'https://api.gamepromo.io/promo/login-client'
    login_headers = {
        'Content-Type': "application/json; charset=utf-8",
        'Connection': "keep-alive",
        'Host': "api.gamepromo.io",
    }
    login_data = {
        "appToken": "d28721be-fd2d-4b45-869e-9f253b554e50",
        "clientId": generate_client_id(),
        "clientOrigin": "deviceid"
    }

    response = requests.post(login_url, headers=login_headers, json=login_data)
    print(response.status_code, response.text)

    client_token = response.json().get("clientToken")
    if not client_token:
        print("Failed to get clientToken")
        return

    
    time.sleep(30)  
    event_url = 'https://api.gamepromo.io/promo/register-event'
    event_headers = {
        'Authorization': f"Bearer {client_token}",
        'Content-Type': "application/json; charset=utf-8",
        'Host': "api.gamepromo.io",
    }
    event_data = {
        "promoId": "43e35910-c168-4634-ad4f-52fd764a843f",
        "eventId": "f838bf3c-f297-43ba-90c8-a23a06473fe1",
        "eventOrigin": "watchad"
    }

    response = requests.post(event_url, headers=event_headers, json=event_data)
    print(response.status_code, response.text)

    retry_count = 0
    max_retries = 5
    while response.json().get("hasCode") is False and retry_count < max_retries:
        time.sleep(30)  
        response = requests.post(event_url, headers=event_headers, json=event_data)
        print(response.status_code, response.text)
        retry_count += 1

    if retry_count == max_retries and response.json().get("hasCode") is False:
        print("Failed to get code after multiple attempts")
        return

    code_url = 'https://api.gamepromo.io/promo/create-code'
    code_headers = {
        'Authorization': f"Bearer {client_token}",
        'Content-Type': "application/json; charset=utf-8",
        'Host': "api.gamepromo.io",
    }
    code_data = {
        "promoId": "43e35910-c168-4634-ad4f-52fd764a843f"
    }

    response = requests.post(code_url, headers=code_headers, json=code_data)
    print(response.status_code, response.text)

    if response.status_code == 200:
        promo_code = response.json().get("promoCode")
        if promo_code:
            with open("keys.txt", "a") as file:
                file.write(f"{promo_code}\n")

num_devices = 40

with ThreadPoolExecutor(max_workers=num_devices) as executor:
    futures = [executor.submit(run_promo_operations) for _ in range(num_devices)]
    for future in as_completed(futures):
        future.result()