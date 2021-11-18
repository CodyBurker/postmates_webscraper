from multiprocessing.context import Process
from selenium import webdriver
import os
import time
import pandas as pd
import re
from datetime import datetime
from selenium.webdriver.common.by import By
import sys
import concurrent.futures
def check_address(address):
    # If windows, use chromdriver.exe otherwise use chromedriver
    if os.name == 'nt':
        chrome_path = os.path.join(os.getcwd(), 'chromedriver.exe')
    else:
        chrome_path = os.path.join(os.getcwd(), 'chromedriver')
    # Set up chrome driver
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
    # each element is a restaurant listing
    for element in elements:
        # Get name
        name_raw = element.find_elements(By.XPATH,"//div[@class='ba c3 bb e2 c5 dn ck ci hp']")
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
    
    # Print list samples 
    # print('Names:{}'.format(names[0:15]))
    # print('Wait Times:{}'.format(wait_times[0:15]))
    # print('Delivery Fees:{}'.format(delivery_fees[0:15]))
    # print('Links:{}'.format(links[0:15]))
    # Print lengths of lists
    # print(len(wait_times), len(delivery_fees), len(names), len(links))
    df = pd.DataFrame({'Name': names, 'Wait Time': wait_times, 'Delivery Fee': delivery_fees, 'Link': links})
    # Remove duplicate listings
    df.drop_duplicates(subset="Link", inplace=True)
    # Remove listings for pickup
    drop_links = [link for link in df.Link if re.search(r'\?deliveryMode=PICKUP$', link)]
    df = df[~df.Link.isin(drop_links)]
    # Close driver
    driver.close()
    # Return dataframe
    return df

# Get data for list of addresses
def get_data(start_address, end_address):
    start = time.time()
    # dataframe of all scraped info for all addresses
    all_address_info = pd.DataFrame()
    with open('OAK_Berk_geocodio.csv') as csvfile:
        file = pd.read_csv(csvfile)
        # filter out less accurate entries (possibly without valid street addresses)
        file = file[~file['Accuracy Type'].isin(["nearest_street", "nearest_place"])]
        # compile list of addresses from file
        addresses = list(file['Number'].astype(int).astype(str)+' '+file['Street']+' '+file['City']+' '+file['State'])
        geoids = list(file['Geoid'])
        if end_address > len(addresses):
            end_address = len(addresses)
        for address in addresses[start_address:end_address]: 
            # dataframe of info for only this address
            df = check_address(address)
            # add delivery address to dataframe
            df['Delivery Address'] = address
            df['Geoid'] = geoids[addresses.index(address)]
            # append individual dataframe to master
            all_address_info = all_address_info.append(df, ignore_index=True)
    print(all_address_info)
    time_written = datetime.now().strftime("%m-%d-%Y %H%M%S")
    addresses = "(%d-%d)" % (start_address, end_address)
    all_address_info.to_csv('scraped_data_raw/postmates_scrape_' + time_written + addresses +  '.csv', index=False)
    end = time.time()
    time_elapsed = end-start
    print("Runtime: ", time_elapsed)

# Generate row numbers to send to threads
# Given a start and end address, and batch size
def generate_row_numbers(start_address, end_address, batch_size):
    # Create list starting at start_address and ending at end_address, counting by batch_size
    address_start = [start_address + i*batch_size for i in range(int((end_address-start_address)/batch_size + 1))]
    # address_start = [i*batch_size for i in range(int(start_address/batch_size), int(end_address/batch_size) + 1)]
    address_end = [i + batch_size for i in address_start]
    # Replace last element iwth end_ad
    address_end[-1] = end_address
    return address_start, address_end



if __name__ == '__main__':

    # Config 
    # start_address: Row to start
    start_address = 0
    # end_address: Row to end at (exclusive)
    end_address = 50
    # batch_size: is number of addresses in each file output
    # Each thread will only handle addresses in batches of batch_size
    batch_size = 10
    # max_workers: is number of threads to run at once, that is number of chrome instances
    max_workers = 5


    # Generate lists of addresses to scrape
    address_start, address_end = generate_row_numbers(start_address, end_address, batch_size=batch_size)
    print("Start Addressses:", str(address_start))
    # Get start time
    start_time = time.time()

    # Set up parallel executor to run threads
    with concurrent.futures.ProcessPoolExecutor(max_workers=max_workers) as executor:
        # Set up threads with start_address and end_address (tell them which addresses to check)
        get_address_dict = {executor.submit(get_data, start_address, end_address): (start_address, end_address) for start_address, end_address in zip(address_start, address_end)}
        for future in concurrent.futures.as_completed(get_address_dict):
            start = get_address_dict[future]
            try:
               future.result()
            except Exception as exc:
                print('%r generated an exception: %s' % (start, exc))

    # Print some summary of speed
    # Print elapsted time in minutes, seconds
    end_time = time.time()
    time_elapsed = end_time-start_time
    # Convert to minutes, seconds
    minutes = int(time_elapsed/60)
    seconds = int(time_elapsed%60)
    print("-------")
    print("Total Runtime: ", minutes, "minutes", seconds, "seconds")
    # Get rate of seconds per address
    rate = time_elapsed/end_address
    print("Seconds per Address: ", rate)
    