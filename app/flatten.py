import  json
from flatten_json import flatten
import os
import pandas as pd
from tqdm import tqdm

from geopandas import GeoDataFrame, points_from_xy

def serach(key,flat_hotel):
    result = [flat_hotel[i] for i in flat_hotel.keys() if key in i]
    if len(result) == 0:
        return None
    
    elif len(result) == 1:
        res =  result[0]
    else:
        res = result[-1]
        
    if isinstance(res,str):
        res = res.replace("€","")
        
    return res

def booking2gpkg():
    directory = "bookingData/"
    files = os.listdir(directory)


    data_collection = {
            "hotel_name" : [],
        "lat" :[],
        "lon" : [],
        "breakdown_price" : [],
        "net_room_price": [],
        "total_price" :[],
        "none_dicount_price" : [],
        "max_persons" : [],
        "roome_type" : [],
        "rating" : [],
        "rating_string" : []
    }



    dataframes  = []   
    for file_name in tqdm(files):
        if file_name.endswith(".json"):
            with open(directory + file_name) as f :
                da_json =  json.loads(f.read())
        
        for idx, hotel in enumerate(da_json["b_hotels"]):
        
            hotel_flat = flatten(hotel)    
            data_dict = {
                "hotel_name" : serach("b_hotel_title",hotel_flat),
                "lat" : serach("latitude",hotel_flat),
                "lon" : serach("longitude",hotel_flat),
                "breakdown_price" : serach("b_availability_b_price_breakdown_b_all_discounts_0_b_value_user_currency",hotel_flat),
                "net_room_price":serach("b_availability_b_price_breakdown_b_net_room_price_0_b_value", hotel_flat),
                "total_price" : serach("b_availability_b_price_breakdown_b_total_price_0_b_value_user_currency",hotel_flat), 
                "none_dicount_price" : serach("b_availability_b_price_breakdown_b_prediscounted_price_average_0_b_value_user_currency",hotel_flat),
                "max_persons" : serach("b_availability_b_blocks_0_b_max_persons",hotel_flat ),
                "roome_type" : serach("b_availability_b_blocks_0_b_room_type",hotel_flat),
                "rating" : serach("b_accommodation_classification_rating_data_rating",hotel_flat),
                "rating_string" : serach("b_review_word",hotel_flat)    
            }  
            
            for k,v in data_dict.items():
                data_collection[k].append(v)
            
    df = pd.DataFrame.from_dict(data_collection)
    geo_df = GeoDataFrame(df, geometry=points_from_xy(df.lon,df.lat)).set_crs("EPSG:4326")
    
    geo_df.to_file("bookingHotels/" + "booking_data.gpkg",driver="GPKG")
    
    print("succesfully saved file!")
  

