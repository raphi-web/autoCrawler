import json
from flatten_json import flatten
import os
import pandas as pd
from tqdm import tqdm
from datetime import datetime
from zipfile import ZipFile


#from geopandas import GeoDataFrame, points_from_xy

def search(key, flat_hotel):
    result = [flat_hotel[i] for i in flat_hotel.keys() if key in i]
    if len(result) == 0:
        return None

    elif len(result) == 1:
        res = result[0]
    else:
        res = result[-1]

    if isinstance(res, str):
        res = res.replace("€", "")
        try:
            res = float(res.replace(",", "."))
        except:
            pass

    return res


def booking2zip():
    directory = "bookingData/"
    files = os.listdir(directory)

    data_collection = {
        "hotel_name": [],
        "hotel_id": [],
        "lat": [],
        "lon": [],
        "address": [],
        "total_price": [],
        "max_persons": [],
        "roome_type": [],
        "rating": [],
        "rating_string": [],
        "date_of_creation":[]
    }

    for file_name in tqdm(files):
        if file_name.endswith(".json"):
            with open(directory + file_name) as f:
                da_json = json.loads(f.read())

        for hotel in da_json["b_hotels"]:

            hotel_flat = flatten(hotel)

            data_collection["hotel_name"].append(search("b_hotel_title", hotel_flat))
            data_collection["hotel_id"].append(search("b_id", hotel_flat))
            data_collection["lat"].append(search("latitude", hotel_flat))
            data_collection["lon"].append(search("longitude", hotel_flat))
            data_collection["address"].append(search("address", hotel_flat))
            data_collection["total_price"].append(search( "b_availability_b_price_breakdown_b_total_price_0_b_value_user_currency", hotel_flat))
            data_collection["max_persons"].append(search("b_availability_b_blocks_0_b_max_persons", hotel_flat))
            data_collection["roome_type"].append(search("b_availability_b_blocks_0_b_room_type", hotel_flat))
            data_collection["rating"].append(search("b_accommodation_classification_rating_data_rating", hotel_flat))
            data_collection["rating_string"].append(search("b_review_word", hotel_flat))
            data_collection["date_of_creation"].append(datetime.now().strftime("%m/%d/%Y"))

    df = pd.DataFrame.from_dict(data_collection)
    df.to_csv("bookingHotels/" + "booking_data.csv", sep=";")
    
    geojson_dict = df2geojson(df)
    geojson_object = json.dumps(geojson_dict)
    with open("bookingHotels/" + "booking_data.geojson","w+") as dst:
        dst.write(geojson_object)
    
    
    with ZipFile("bookingHotels/booking_data.zip","w") as zip_file:
        print(os.listdir("bookingHotels/"))
        for file  in os.listdir("bookingHotels/"):
                if file.endswith(".csv") or file.endswith(".geojson"):
                    zip_file.write("bookingHotels/" + file)
    

    print("succesfully saved file!")

def row2feature(df_row, columns):
    
    template_feature =   { "type": "Feature", "properties": {}, "geometry": {} }
    properties = {}
    
    for row in columns:
        properties[row] = df_row[row]
        
    template_feature["properties"] = properties
    geometry = { "type": "Point", "coordinates": [df_row.lon, df_row.lat ] }
    template_feature["geometry"] = geometry

    
    return template_feature


def df2geojson(df):
    template = """{
    "type": "FeatureCollection",
    "name": "test",
    "crs": { "type": "name", "properties": { "name": "urn:ogc:def:crs:OGC:1.3:CRS84" } },
    "features": []
    }
    """

    template_json = json.loads(template)
    
    for _,row in df.iterrows():
        template_json["features"].append(row2feature(row,df.columns))
        
        
    return template_json
        
        
if __name__=="__main__":
    booking2zip()
    
        
