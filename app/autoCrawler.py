import os
from flask import render_template, request, abort, send_file
from flask.app import Flask
import time
import threading
import sys
from seleniumwire import webdriver
from selenium.webdriver.common.by import By
import numpy as np
import brotli
import json
import uuid
from flask_socketio import SocketIO
from selenium.common.exceptions import WebDriverException
from flatten import booking2gpkg
from geventwebsocket import WebSocketServer
from engineio.async_drivers import gevent  # requirement for pyinstaller

#from socket import socket
# requirements for address extraction
import requests
from bs4 import BeautifulSoup
from difflib import SequenceMatcher
import asyncio

# span[class="d543a27a3a"]
# div[data-testid="map-trigger"]

app = Flask(__name__)
socketio = SocketIO(app)
app.config['SECRET_KEY'] = 'secret!'

print("Copy Geckodriver to this Folder:\n", os.getcwd(), "\n\n")

def update_page_status(message):
    socketio.emit('my_response', {'data': message})

@socketio.on("connection")
def send_conection_message(_):
    print("Connected to client!")
  

@socketio.on("clear")
def clear_folder(_):
    print("Cleared!")
    try:
        for f in os.listdir("bookingData"):
            os.remove(f"bookingData/{f}")
    except Exception as e:
        print("Error deleting files")
        print(e)

@socketio.on("gpkg")
def files2gpkg(_):
    try:
        print("Prepering Data")
        booking2gpkg()
        clear_folder("")

        socketio.emit('download_ready', {'data': "download_ready"})
    except Exception as e:
        print("Error Creating Geopackege")
        print(e)
        update_page_status(str(e))
        if len(os.listdir("bookingHotels")) > 0:
            socketio.emit('download_ready', {'data': "download_ready"})



   
@app.route("/")
def root():
    return render_template("index.html")

@app.route("/start", methods=["POST"])
def start_collecting():
    nxt_pg_btn = request.form["nxt_pg_btn"]
    map_btn = request.form["map_btn"]
    close_map_btn = request.form["close_map_btn"]
    json_name = request.form["req_name"]

    address_check = request.form["address"] == "yes"
    driver.switch_to.window(tabs[-1])

    socketio.emit('start_collecting', {'data': "start_collecting"})

    threading.Thread(target=booking_collect, args=(
        nxt_pg_btn, map_btn, close_map_btn, json_name, address_check)).start()

    return "ok"

@app.route('/get-files/booking_data.gpkg', methods=['GET', 'POST'])
def get_files():
    path = os.getcwd()
    file = path + "/bookingHotels/booking_data.gpkg"
    try:
        return send_file(file, as_attachment=True)
    except Exception as e:
        print(e)
        abort(404)


def start_server():
    host = "127.0.0.1"
    port = 5000
    http_server = WebSocketServer((host, port), app)
    http_server.serve_forever()


def booking_collect(nxt_pg_btn, map_btn, close_map_btn, json_name, address_check):
    page = 0

    try:
        next_page_btn = driver.find_element(By.CSS_SELECTOR, nxt_pg_btn)
        while next_page_btn.get_attribute("disabled") == None:

            driver.switch_to.window(tabs[-1])
            driver.find_element(By.CSS_SELECTOR, map_btn).click()

            # gather adresses whilde the hotel data request loads
            if address_check:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                hotel_addresses = loop.run_until_complete(get_addresses())
                hotel_addr_keys = list(hotel_addresses.keys())

            try:
                hotel_response = None
                max_wait = 30
                second_counter = 0
                while hotel_response == None and second_counter < max_wait:
                    time.sleep(1)
                    second_counter += 1
                    filterd_requests = [
                        i for i in driver.requests if json_name in i.url]

                    if len(filterd_requests) > 0:
                        hotel_response = filterd_requests[0].response

                response_json = brotli.decompress(
                    hotel_response.body).decode("utf-8")
                response_json = json.loads(response_json)

                if address_check:
                    for idx, hotel in enumerate(response_json["b_hotels"]):
                        hotel_name = hotel["b_hotel_title"]
                        for addr_idx, hotel_addr_name in enumerate(hotel_addr_keys):
                            if similar(hotel_addr_name, hotel_name) > 0.8:
                                response_json["b_hotels"][idx]["address"] = hotel_addresses[hotel_addr_name]
                                hotel_addr_keys.pop(addr_idx)

                unique_filename = str(uuid.uuid4())
                with open(f"bookingData/{unique_filename}.json", "w") as f:
                    json.dump(response_json, f)

                print("saved json", page)
                update_page_status(
                    f"Saved Data from page {page} with id: {unique_filename}")

            except Exception as e:
                print("Error Collecting Request!", e)
                update_page_status(str(e))

            driver.find_element(By.CSS_SELECTOR, close_map_btn).click()
            time.sleep(np.random.choice([x for x in range(3, 9)]))
            next_page_btn = driver.find_element(By.CSS_SELECTOR, nxt_pg_btn)
            next_page_btn.click()
            del driver.requests
            page += 1
            time.sleep(np.random.choice([x for x in range(3, 11)]))

        socketio.emit("finished_collecting", {'data': "finished_collecting"})

    except WebDriverException as e:
        update_page_status(f"ERROR-" + str(e))
        sys.exit()


async def get_addresses():
    async def request_hotels(link):
        try:
            hotel_soup = BeautifulSoup(requests.get(
                link).content.decode("utf-8"), features="html.parser")
            hotel_name = hotel_soup.find(id="hp_hotel_name")
            hotel_name.find("span").clear()
            hotel_name = hotel_name.text.replace("\n", "")
            hotel_address = hotel_soup.find(
                class_="hp_address_subtitle").text.replace("\n", "")
            name_address[hotel_name] = hotel_address
        except Exception as e:
            update_page_status("Error collecting, adress for one Hotel: " + str(e))
            print("Error collecting, adress for one Hotel: " + str(e))
            pass
            
        return 0
    name_address = {}
    try:
        soup = BeautifulSoup(driver.page_source, features="html.parser")
        anchor_tags = soup.select('a[data-testid="title-link"]')

        tasks = []
        for anchor in anchor_tags:
            link = anchor.get("href")
            tasks.append(request_hotels(link))

        await asyncio.gather(*tasks)
    except Exception as e:
        print(e)
        update_page_status("Error getting Adress: " + str(e))
        pass
    return name_address


def similar(a, b):
    return SequenceMatcher(None, a, b).ratio()


try:
    os.mkdir("bookingData")
except FileExistsError:
    pass

try:
    os.mkdir("bookingHotels")
except FileExistsError:
    pass

driver_name = "./geckodriver"
sys.path.append(driver_name)

driver = webdriver.Firefox(executable_path=driver_name)
th = threading.Thread(target=start_server)
th.start()

update_page_status("Logs will be displayed here!")

driver.get("http://127.0.0.1:5000/")
driver.execute_script("window.open()")

tabs = driver.window_handles
driver.switch_to.window(tabs[-1])


driver.get('https://www.booking.com/')
time.sleep(1)
driver.switch_to.window(tabs[0])
th.join()

