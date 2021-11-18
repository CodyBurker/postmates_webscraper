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

    print(df.Link)


    for link in df.Link:
        driver.get(link)

        action = ActionChains(driver)
        action.send_keys(Keys.ESCAPE);
        action.perform()

        distances = driver.find_elements_by_xpath("//p[@class='ba bv dm bw bx']")
        distances = [distance.text for distance in distances]
        distances = re.split("\n",distances[0])[0]
        addresses.append(distances)
    
    # Close driver
    driver.close()
    df['Restaurant Address'] = addresses
    
    #Forward geocoding restaurant address
    api_key = "dd044ee1e656909e96c479030d3c087a"
    # Forward Geocoding API Endpoint
    query = {"access_key" : api_key, "query" : "1600 Pennsylvania Ave NW, Washington DC"}
    response = requests.get('http://api.positionstack.com/v1/forward', params = query)
    print(response.json())
    #Documentation: https://positionstack.com/documentation
    
    # Loading the lat-long data for restaurant & delivAddress
    restaurant = (22.5726, 88.3639)
    delivAddress = (28.7041, 77.1025)
    
    # Print the distance calculated in miles
    print(geodesic(restaurant, delivAddress).mi)
    
    # Return dataframe
    return df


if __name__ == '__main__':
    with open('postmates_scrape.csv') as csvfile:
        file = pd.read_csv(csvfile)
        df = get_distance(file)
    print(df)
    # price = get_price(link)
    # print(f"Resteraunt: {df.iloc[0]['Name']}")
    # print(f"Price: {price}")
