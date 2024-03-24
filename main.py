import random
import time
import requests
import helpers

BASE_URL, USERNAME, PASSWORD, PROXY_URL, x_, y_ = helpers.read_config("config.txt")

LOGIN_API = "/api/v1/auth/login"
AUTH_API = "/api/v1/auth/"
MAIN_PAGE = "/dorf1.php"
MAP_PAGE = "/karte.php"
MAP_API = "/api/v1/map/position"

proxies = {
    "http": PROXY_URL,
    "https": PROXY_URL,
}
oasis_output_path = "oasis.txt"
best_places_path = "best_places.txt"
executed_coords_output_path = "executed.txt"
response_path = "responses.txt"
valley_path = "valley.txt"
crop_path = "crops/crops.txt"


def login(base_url, username, password):
    login_url = f"{base_url}{LOGIN_API}"
    headers = {
        'Content-Type': 'application/json; charset=UTF-8',
        'X-Requested-With': 'XMLHttpRequest',
        'Host': base_url.split('//')[1],  # Extract the host from the base_url
        'Connection': 'keep-alive',
        'sec-ch-ua': '"Chromium";v="104", " Not A;Brand";v="99", "Google Chrome";v="104"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'Origin': base_url,
        'Sec-Fetch-Site': 'same-origin',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Dest': 'empty',
        'Referer': base_url + '/logout',
        'Accept-Encoding': 'gzip, deflate, br, zstd',
        'Accept-Language': 'tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7,la;q=0.6',
        'User-Agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                      "(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36 Edg/122.0.0.0"
    }
    data = {"name": username, "password": password, "w": "1920:1080", "mobileOptimizations": False}
    session = requests.Session()
    if proxies is not None:
        session.proxies = {
            "http": PROXY_URL,
            "https": PROXY_URL,
        }
        print(f'Your proxy ip adress: {session.get("http://httpbin.org/ip").text}')

    response = session.post(login_url, headers=headers, json=data)
    if response.status_code == 200 and 'nonce' in response.json():
        nonce = response.json()["nonce"]
        auth_url = f"{base_url}{AUTH_API}{nonce}"
        headers["Upgrade-Insecure-Requests"] = '1'
        headers['Sec-Fetch-Mode'] = "navigate"
        headers['Sec-Fetch-User'] = '?1'
        headers['Sec-Fetch-Dest'] = "document"
        headers['Accept'] = "text/html,application/xhtml+xml,application/xml;q=0.9,image/" \
                            "avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7"

        auth_response = session.post(auth_url, headers=headers)
        if auth_response.status_code == 200 and 'token' in auth_response.json():
            token = auth_response.json()["token"]
            print("Login successful.")
            headers['Authorization'] = f'Bearer {token}'
            session.headers.update(headers)
            return session, token, headers
    print("Login failed.")
    return None, None, None


def get_map_data(headers, session, x, y):
    map_api_url = f"{BASE_URL}{MAP_API}"
    data = {"data": {"x": x, "y": y, "zoomLevel": 3, "ignorePositions": []}}
    response = session.post(map_api_url, headers=headers, json=data)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Failed to get map data: {response.status_code}")
        return None


def get_all_coordinates(headers, session, update):
    corPoints = list(range(-180, 181, 30))  # Simplified range for demonstration
    headers['Sec-Fetch-Dest'] = 'empty'
    headers['Sec-Fetch-Mode'] = 'cors'
    headers['Accept'] = 'application/json, text/javascript, */*; q=0.01'
    if update:
        open(oasis_output_path, 'w').close()
        open(executed_coords_output_path, 'w').close()
        open(response_path, 'w').close()
    for x in corPoints:
        for y in corPoints:
            api_response_data = get_map_data(headers, session, x, y)
            headers['Referer'] = f'{BASE_URL}{MAP_PAGE}?x={x}&y={y}'
            if api_response_data:
                helpers.find_oasis(api_response_data, oasis_output_path, executed_coords_output_path)
                helpers.write_response(response_path, api_response_data)
            time.sleep(random.uniform(1, 3))  # Random sleep to mimic human behavior


def request_step(update=True):
    session, token, headers = login(BASE_URL, USERNAME, PASSWORD)
    time.sleep(random.uniform(2.2, 2.4))

    session.get(f"{BASE_URL}{MAIN_PAGE}")
    headers['referer'] = BASE_URL + MAIN_PAGE
    time.sleep(random.uniform(4, 6))
    session.get(f"{BASE_URL}{MAP_PAGE}")
    time.sleep(0.2)
    headers['referer'] = BASE_URL + MAP_PAGE
    session.headers.update(headers)
    time.sleep(random.uniform(1.5, 2.5))
    if session and token:
        get_all_coordinates(headers, session, update)
    else:
        print("Session or token not established.")


def main():
    print("*********************WELCOME TO TRAVIAN LEGENDS OASIS FINDER!!!*********************\n\n")
    while True:
        global x_
        global y_
        if not x_ and not y_:
            x_ = int(input("If you do not want to be asked the following questions each time, "
                           "edit the places where x=0 and y=0 in config.txt according to the coordinate you want.\n\n"
                           "Enter your X coordinate first to see the menu: "))

            y_ = int(input("Enter your Y coordinate to see the menu: "))

        print("\n******************************************MENU******************************************\n")
        choice = input("1-) If you want to fetch or update the map (number of animals, player populations)\n"
                       "2-) To get an Excel output of the number of animals in the oasis\n"
                       "3-) To find the nearest 15s\n"
                       "4-) To get a list of the best places to throw distant villages\n"
                       "5-) To get an Excel of the best places\n"
                       "6-) To exit the program\n"
                       "\nType the number of your choice: ")

        if choice == "1":
            request_step()
            helpers.process_tiles(response_path, valley_path)
            helpers.find_crops(valley_path, oasis_output_path, crop_path)
            helpers.sort_and_rewrite_valleys(valley_path, x_, y_)
        elif choice == "2":
            algo = int(input(
                "Press 1 to sort according to the most logical Oasis order or 2 to sort according to distance."))
            helpers.sort_and_rewrite_oases(oasis_output_path, x_, y_, algo)
            helpers.oasis_to_excel(oasis_output_path, BASE_URL, x_, y_)
            break
        elif choice == "3":
            helpers.crops_to_excel(crop_path, x_, y_, int(input("How many percent of Grain 15s should be shown: ")))
        elif choice == "4":
            pass
            break
        elif choice == "5":
            helpers.best_places_finder(oasis_output_path, best_places_path)
            break
        elif choice == "6":
            print("Closing the program.")
            break
        else:
            print("Invalid choice. Please try again.")


if __name__ == "__main__":
    main()
