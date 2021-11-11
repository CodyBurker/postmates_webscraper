from selenium import webdriver
from selenium.webdriver.common.keys import Keys
import os
import time
import pandas as pd
import re
import numpy as np

def get_distance(address, file):
    # Chrome path
    chrome_path = os.path.join(os.getcwd(), 'chromedriver')
    # Set up chrome driver
    options = webdriver.ChromeOptions()
    options.add_experimental_option('excludeSwitches', ['enable-logging'])
    driver = webdriver.Chrome(executable_path=chrome_path, options=options)

    df = file
    df['Distance to Delivery'] = np.NaN

    # print(df.Link)


    for link in df.Link:
        driver.get(df.Link[0])
        # Enter address in pop up window
        element = driver.find_element_by_id("location-typeahead-location-manager-input")
        element.send_keys(address)
        element.send_keys(Keys.ENTER) # isn't working -- don't know why
        time.sleep(5)
        # Get distance to restaurant from address
        distances = driver.find_elements_by_xpath("//div[@class='ba ko bb bw bx er']")
        print(distances)
        distances = [distance.text for distance in distances]
        print(distances)
        distance_pattern = re.compile(r"[0-9]*[0-9].?[0-9]?\smi")
        # Save distance to updated df
        for distance in distances:
            if distance != '' and re.search(distance_pattern, distance):
                print("in if condition")
                df[df['Link'] == link]['Distance to Delivery'] = distance
    
    # Close driver
    driver.close()
    # Return dataframe
    return df


if __name__ == '__main__':
    with open('postmates_scrape.csv') as csvfile:
        file = pd.read_csv(csvfile)
        df = get_distance("1 Apple Way", file)
    print(df)
    # price = get_price(link)
    # print(f"Resteraunt: {df.iloc[0]['Name']}")
    # print(f"Price: {price}")