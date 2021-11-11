from selenium import webdriver
from selenium.webdriver.common.keys import Keys
import os
import time
import pandas as pd
import re
import numpy as np

def get_distance(address, file):
    ''' Parameters -- 
    Address (string): Delivery address
    File (Pandas DataFrame): Scraped info pertaining to address. 0-indexed. 
    
    Returns a dataframe identical to file with "Distance to Delivery" column 
        populated for address.
    '''
    # Chrome path
    chrome_path = os.path.join(os.getcwd(), 'chromedriver')
    # Set up chrome driver
    options = webdriver.ChromeOptions()
    options.add_experimental_option('excludeSwitches', ['enable-logging'])
    driver = webdriver.Chrome(executable_path=chrome_path, options=options)

    distances = []

    for link in file.Link:
        driver.get(link)
        time.sleep(2)
        # Enter address in pop up window for first restaurant only
        if file.index[file.Link == link] == 0:
            textbox = driver.find_element_by_id("location-typeahead-location-manager-input")
            textbox.send_keys(address)
            time.sleep(1)
            textbox.send_keys(Keys.RETURN)
            time.sleep(2)

        # Get distance to address from restaurant
        raw_text = driver.find_element_by_id("main-content")
        distance_pattern = re.compile(r"[0-9]*[0-9].?[0-9]?\smi\b")
        # Save distances or N/A if no distance is listed
        if re.search(distance_pattern, raw_text.text):
            distances.append(re.search(distance_pattern, raw_text.text).group(0))
        else:
            distances.append("N/A")
    # add distances to dataframe
    file['Distance to Delivery'] = distances

    # Close driver
    driver.close()
    # Return dataframe
    return file

if __name__ == '__main__':
    with open('postmates_scrape.csv') as csvfile:
        file = pd.read_csv(csvfile)
        file = get_distance("2444 Dole St, Honolulu, HI 96822", file)
    print(file)
    # price = get_price(link)
    # print(f"Resteraunt: {file.iloc[0]['Name']}")
    # print(f"Price: {price}")