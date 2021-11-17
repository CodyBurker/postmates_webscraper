from selenium import webdriver
import os
import time
import pandas as pd
import re
import docker
import logging

import selenium

# Set up logging to file
logging.basicConfig(filename='posty2_redo.log', level=logging.DEBUG)

def check_address(address, chrome_port = None):

    # If on windows use chromedriver.exe
    if os.name == 'nt':
        chrome_path =os.path.join(os.getcwd(), 'chromedriver.exe')
    # Else on linux use chromedriver
    else:
        chrome_path =os.path.join(os.getcwd(), 'chromedriver')
    # Set up chrome driver
    # Chrome path
    if chrome_port is not None:
        # Set up remote driver on port chrome_port
        driver = webdriver.Remote()
    else:
        options = webdriver.ChromeOptions()
        options.add_experimental_option('excludeSwitches', ['enable-logging'])
        driver = webdriver.Chrome(executable_path=chrome_path, options=options)
    driver.get("https://postmates.com/")
    # Get element with id=location-typeahead-home-input
    element = driver.find_element_by_id("location-typeahead-home-input")
    # Enter text in element
    element.send_keys(address)
    # Get button with text="Find Food"
    time.sleep(1)
    button = driver.find_element_by_xpath("//button[text()='Find Food']")
    # Click button
    button.click()
    # Wait for page to load
    time.sleep(7)
    # Get list of results
    raw_links = driver.find_elements_by_xpath("//div[@class='ag ci']/a")
    links = [link.get_attribute('href') for link in raw_links]
    elements = driver.find_elements_by_xpath("//div[@class='ag ci']")
    # print(elements)
    names = []
    wait_times = []
    delivery_fees = []
    # Log got number of elements
    logging.info('Got %s elements' % len(elements))
    # each element is a restaurant listing
    for element in elements:
        # Get name
        name_raw = element.find_elements_by_xpath(".//div[@class='ba c3 bb e2 c5 dn ck ci ho']")
        if name_raw:
            names.append(name_raw[0].text)
        else:
            names.append("N/A")

        # Get delivery fee
        delivery_fee = element.find_elements_by_xpath(".//div[@class='ck ci br']")
        delivery_fee = [fee.text for fee in delivery_fee]
        # Checks which element of this class is the delivery fee (icon is in same class)
        index = [idx for idx, s in enumerate(delivery_fee) if '$' in s]
        # empty index string means there is no delivery fee listed
        if index:
            delivery_pattern = re.compile(r"([0-9]*[0-9].?([0-9][0-9])?)")
            delivery_fee = re.search(delivery_pattern, delivery_fee[index[0]]).group(0)
            delivery_fees.append(delivery_fee)
        else:
            delivery_fees.append("N/A")

        # Get wait time
        wait_time = element.find_elements_by_xpath(".//div[@class='ck ci ho']")
        wait_time = [wait.text for wait in wait_time]
        # Leaves "Currently unavailable" and "Too far to deliver" as possible values
        if wait_time:
            if wait_time[0] != '' and len(wait_time) > 0:
                wait_times.append(wait_time[0])
            else:
                wait_times.append("N/A")
        else:
            wait_times.append("N/A")

    df = pd.DataFrame({'Name': names, 'Wait Time': wait_times, 'Delivery Fee': delivery_fees, 'Link': links})
    # Remove duplicate listings
    df.drop_duplicates(subset="Link", inplace=True)
    # Remove listings for pickup
    drop_links = [link for link in df.Link if re.search(r'\?deliveryMode=PICKUP$', link)]
    df = df[~df.Link.isin(drop_links)]
    # Close driver
    # driver.close()
    # Return dataframe
    return df

if __name__ == '__main__':
    start = time.time()
    # dataframe of all scraped info for all addresses
    all_address_info = pd.DataFrame()
    with open('OAK_Berk_geocodio.csv') as csvfile:
        file = pd.read_csv(csvfile)
        # filter out less accurate entries (possibly without valid street addresses)
        file = file[~file['Accuracy Type'].isin(["nearest_street", "nearest_place"])]
        # compile list of addresses from file
        addresses = list(file['Number'].astype(int).astype(str)+' '+file['Street']+' '+file['City']+' '+file['State'])
        for address in addresses[0:11]: # FOR DEV: only first 10 addresses
            # dataframe of info for only this address
            df = check_address(address)
            # add delivery address to dataframe
            df['Delivery Address'] = address
            # append individual dataframe to collective
            all_address_info = all_address_info.append(df, ignore_index=True)
    print(all_address_info)
    all_address_info.to_csv('postmates_scrape.csv', index=False)
    end = time.time()
    time_elapsed = end-start
    print("Runtime: ", time_elapsed)
    # price = get_price(link)
    # print(f"Resteraunt: {df.iloc[0]['Name']}")
    # print(f"Price: {price}")