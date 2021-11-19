from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
import os
import time
import pandas as pd
import re
import numpy as np
from geopy.distance import geodesic
import requests
import json

def get_distance(file):
    # Chrome path
    chrome_path = os.path.join(os.getcwd(), 'chromedriver.exe')
    # Set up chrome driver
    options = webdriver.ChromeOptions()
    options.add_experimental_option('excludeSwitches', ['enable-logging'])
    driver = webdriver.Chrome(executable_path=chrome_path, options=options)

    df = file
    addresses = []
    latitudes = []
    longitudes = []
    distance = []

    print(df.Link)
    
    #Forward geocoding restaurant address
    api_key = "dd044ee1e656909e96c479030d3c087a"

    for ind in df.index:
        link = df['Link'][ind]
        driver.get(link)

        action = ActionChains(driver)
        action.send_keys(Keys.ESCAPE);
        action.perform()

        distances = driver.find_elements(By.XPATH,".//p[@class='ba bv do bw bx']")
        distances = [distance.text for distance in distances]
        #print(distances)
        distances = re.split("\n",distances[0])[0]
        #print(distances)
        addresses.append(distances)
        
        # Forward Geocoding API Endpoint
        query = {"access_key" : api_key, "query" : distances, "limit" : 1}
        response = requests.get('http://api.positionstack.com/v1/forward', params = query)
        jsonRest = (response.json())
        #Documentation: https://positionstack.com/documentation
        
        #Get latitude and longitude from json data
        latLong = jsonRest['data']
        #print(latLong)
        latLong = latLong[0]
        lat = latLong['latitude']
        #print(lat)
        latitudes.append(lat)
        long = latLong['longitude']
        #print(long)
        longitudes.append(long)
        
        # Get the distance calculated in miles
        restaurant = (lat, long)
        #print("Restaurant address: ", restaurant)
        delivAddress = (df['Latitude'][ind], df['Longitude'][ind])
        #print("Delivery address: ", delivAddress)
        dist = geodesic(restaurant, delivAddress).mi
        #print("Distance: ", dist)
        distance.append(dist)
    
    # Close driver
    driver.close()
    df['Restaurant Address'] = addresses
    df['Restaurant Latitude'] = latitudes
    df['Restaurant Longitude'] = longitudes 
    df['Distance'] = distance
    
    # Return dataframe
    return df


if __name__ == '__main__':
    start = time.time()
    with open('postmates_scrape.csv') as csvfile:
        file = pd.read_csv(csvfile)
        df = get_distance(file)
    print(df)
    df.to_csv('distance_scrape.csv', index=False)
    end = time.time()
    time_elapsed = end-start
    print("Runtime: ", time_elapsed)
