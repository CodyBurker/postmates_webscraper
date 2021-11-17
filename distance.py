from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import NoSuchElementException
import os
import time
import pandas as pd
import re
import numpy as np

def get_distance(address, file):
    ''' Parameters -- 
    Address (string): Delivery address
    File (Pandas DataFrame): Scraped info pertaining to address. 
    
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
        try:
            textbox = driver.find_element_by_id("location-typeahead-location-manager-input")
            textbox.send_keys(address)
            time.sleep(1)
            textbox.send_keys(Keys.RETURN)
            time.sleep(2)
        except NoSuchElementException:
            pass
        # Get distance to address from restaurant
        raw_text = driver.find_element_by_id("main-content")
        distance_pattern = re.compile(r"[0-9]*[0-9].?[0-9]?\smi\b")
        # Save distance or N/A if no distance is listed/restaurant is closed
        if re.search(distance_pattern, raw_text.text):
            distances.append(re.search(distance_pattern, raw_text.text).group(0))
        else:
            distances.append("N/A")
    # Close driver
    driver.close()
    # Return list
    return distances

if __name__ == '__main__':
    with open('postmates_scrape.csv') as csvfile:
        file = pd.read_csv(csvfile)
        # initialize distance column
        file['Distance'] = np.NaN
        for address in file['Delivery Address'].unique()[0:1]: # For dev: testing one address only
            # get distances from each restaurant to this address
            distances = get_distance(address, file[file['Delivery Address'] == address])
            # save those distances to file dataframe
            file['Delivery Address' == address, 'Distance'] = distances
    print(file)
    # price = get_price(link)
    # print(f"Resteraunt: {file.iloc[0]['Name']}")
    # print(f"Price: {price}")