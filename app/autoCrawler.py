import os
from socket import socket
from flask import render_template, request, send_from_directory
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
from engineio.async_drivers import gevent # requirement for pyinstaller
app = Flask(__name__)
socketio = SocketIO(app)

app.config['SECRET_KEY'] = 'secret!'

print("Copy Geckodriver to this Folder:\n", os.getcwd(), "\n\n")

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
        update_page_status("Processing Data this can take a while...")
        booking2gpkg()
        clear_folder("")
        
        socketio.emit('download_ready', {'data': "download_ready"})
    except Exception as e:
        print("Error Creating Geopackege")
        print(e)
        update_page_status(str(e))
        if len(os.listdir("bookingHotels")) > 0:
            socketio.emit('download_ready', {'data': "download_ready"})
            
def update_page_status(message):
    socketio.sleep(10)
    socketio.emit('my_response', {'data': message})

@app.route("/")
def root():
    return render_template("index.html")

@app.route("/start", methods=["POST"])
def start_collecting():
    nxt_pg_btn = request.form["nxt_pg_btn"]
    map_btn = request.form["map_btn"]
    close_map_btn = request.form["close_map_btn"]
    json_name = request.form["req_name"]

    driver.switch_to.window(tabs[-1])
    socketio.emit('start_collecting', {'data': "start_collecting"})

    threading.Thread(target=booking_collect, args=(
        nxt_pg_btn, map_btn, close_map_btn, json_name)).start()

    return "ok"


@app.route('/get-files/booking_data.gpkg',methods = ['GET','POST'])
def get_files():
    try:
        return send_from_directory("bookingHotels/","booking_data.gpkg",as_attachment=True)
    except Exception as e:
        print(e)
        update_page_status(str(e))
        
def start_server():
    host = "127.0.0.1"
    port = 5000

    http_server = WebSocketServer((host, port), app)
    http_server.serve_forever()

def booking_collect(nxt_pg_btn, map_btn, close_map_btn, json_name):
    page = 0
    try:
        next_page_btn = driver.find_element(By.CSS_SELECTOR, nxt_pg_btn)
        while next_page_btn.get_attribute("disabled") == None:

            driver.switch_to.window(tabs[-1])

            driver.find_element(By.CSS_SELECTOR, map_btn).click()
            time.sleep(np.random.choice([x for x in range(3, 12)]))
            try:
                hotel_request = [
                    i for i in driver.requests if json_name in i.url][0]
                response = hotel_request.response

                response = brotli.decompress(response.body).decode("utf-8")
                response = json.loads(response)
                unique_filename = str(uuid.uuid4())
                with open(f"bookingData/{unique_filename}.json", "w") as f:
                    json.dump(response, f)

                print("saved json", page)
                update_page_status(
                    f"Saved Data from page {page} with id:{unique_filename}")

            except Exception as e:
                print("Error Collecting Request!",e)
                update_page_status(str(e))
                
            driver.find_element(By.CSS_SELECTOR, close_map_btn).click()
            time.sleep(np.random.choice([x for x in range(1, 10)]))
            next_page_btn = driver.find_element(By.CSS_SELECTOR, nxt_pg_btn)

            next_page_btn.click()
            del driver.requests
            page += 1
            time.sleep(np.random.choice([x for x in range(7, 22)]))

    except WebDriverException as e:
        update_page_status(f"ERROR-" + str(e))
        sys.exit()

    update_page_status(f"Done!")


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


driver.get("http://127.0.0.1:5000/")
driver.execute_script("window.open()")

tabs = driver.window_handles
driver.switch_to.window(tabs[-1])

driver.get('https://www.booking.com/')
time.sleep(1)
driver.switch_to.window(tabs[0])
th.join()
