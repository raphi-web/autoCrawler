import  json
from flatten_json import flatten
import os
import pandas as pd
from tqdm import tqdm

from geopandas import GeoDataFrame, points_from_xy

def search(key,flat_hotel):
    result = [flat_hotel[i] for i in flat_hotel.keys() if key in i]
    if len(result) == 0:
        return None
    
    elif len(result) == 1:
        res =  result[0]
    else:
        res = result[-1]
        
    if isinstance(res,str):
        res = res.replace("€","")
        try:
             res = float(res.replace(",","."))
        except:
            pass
            
        
    return res

def booking2gpkg():
    directory = "bookingData/"
    files = os.listdir(directory)


    data_collection = {
        "hotel_name" : [],
        "hotel_id":[],
        "lat" :[],
        "lon" : [],
        "address":[],
        "total_price" :[],
        "max_persons" : [],
        "roome_type" : [],
        "rating" : [],
        "rating_string" : []
    }


     
    for file_name in tqdm(files):
        if file_name.endswith(".json"):
            with open(directory + file_name) as f :
                da_json =  json.loads(f.read())
        
        for hotel in da_json["b_hotels"]:
        
            hotel_flat = flatten(hotel)    
            data_dict = {
                "hotel_name" : search("b_hotel_title",hotel_flat),
                "hotel_id" : search("b_id", hotel_flat),
                "lat" : search("latitude",hotel_flat),
                "lon" : search("longitude",hotel_flat),
                "address": search("address",hotel_flat),
                "total_price" : search("b_availability_b_price_breakdown_b_total_price_0_b_value_user_currency",hotel_flat), 
                "max_persons" : search("b_availability_b_blocks_0_b_max_persons",hotel_flat ),
                "roome_type" : search("b_availability_b_blocks_0_b_room_type",hotel_flat),
                "rating" : search("b_accommodation_classification_rating_data_rating",hotel_flat),
                "rating_string" : search("b_review_word",hotel_flat)    
            }  
            
            for k,v in data_dict.items():
                data_collection[k].append(v)
            
    df = pd.DataFrame.from_dict(data_collection)
    geo_df = GeoDataFrame(df, geometry=points_from_xy(df.lon,df.lat)).set_crs("EPSG:4326")
    
    geo_df.to_file("bookingHotels/" + "booking_data.gpkg",driver="GPKG")
    
    print("succesfully saved file!")