from selenium import webdriver
import os
import time
import pandas as pd
import re

'''11/5 elise changed: f-string formatting in lines 47-49, sort results page 
by most popular instead of delivery time, add delivery fee column to dataframe,
update xpaths to relevant elements
'''

# the affiliated icon, 
# restaurant name, 
# distance to you, 
# time to deliver, 
# price

def check_address(address):

    # Chrome path
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
    time.sleep(2)
    button = driver.find_element_by_xpath("//button[text()='Find Food']")
    # Click button
    button.click()
    # Wait for page to load
    time.sleep(10)
    # Get list of results
    names_raw = driver.find_elements_by_xpath("//h3")
    # Parse names
    names = [name.text for name in names_raw]
    # Get link to each result page where dev class='ag ci' with child a href
    links_raw = driver.find_elements_by_xpath("//div[@class='ag ci']/a")
    # Parse links
    links = [link.get_attribute('href') for link in links_raw]
    # Get list of wait times
    # ORIGINAL: 
    # wait_times = driver.find_elements_by_xpath("//div[@class='ba bv e1 bw bx fe']")
    # Worked on Delivery Time filter page
    # wait_times = driver.find_elements_by_xpath("//div[@class='ba bv e1 bw bx ff']")
    wait_times = driver.find_elements_by_xpath("//div[@class='ck ci ho']")
    # Parse wait times
    wait_times = [wait_time.text for wait_time in wait_times]

    # Exclude empty strings
    wait_times = [wait_time for wait_time in wait_times if wait_time != '']

    delivery_fees = driver.find_elements_by_xpath("//div[@class='ck ci br']")
    delivery_fees = [fee.text for fee in delivery_fees]
    # delivery_fees = [fee for fee in delivery_fees if fee != ''] # verify that regex doesn't exclude any restaurant entries
    delivery_fees = [re.search(r"[0-9]*[0-9].[0-9][0-9]", fee).group(0) for fee in delivery_fees if fee != '' and re.search(r"[0-9]*[0-9].[0-9][0-9]", fee)]
    # Print length of lists
    print('Names:{}'.format(names[0:15]))
    print('Wait Times:{}'.format(wait_times[0:15]))
    print('Delivery Fees:{}'.format(delivery_fees[0:15]))
    print('Links:{}'.format(links[0:15]))
    print(len(names), len(wait_times), len(delivery_fees), len(links))

    # print(ratings[0:15])

    # Combine  names, wait times, and links into a dataframe
    df = pd.DataFrame({'Name': names, 'Wait Time': wait_times, 'Delivery Fee': delivery_fees, 'Link': links})

    # Close driver
    driver.close()
    # Return dataframe
    return df

# # Given link to restaurant page, return delivery fee
# def get_price(link):
#     # Chrome path
#     chrome_path = os.path.join(os.getcwd(), 'chromedriver')
#     # Set up chrome driver
#     options = webdriver.ChromeOptions()
#     options.add_experimental_option('excludeSwitches', ['enable-logging'])
#     driver = webdriver.Chrome(chrome_path, options=options)
#     driver.get(link)
#     # Get fee
#     fee = driver.find_element_by_xpath("//span[@class='ah bh']").text
#     # Close driver
#     driver.close()
#     return fee


if __name__ == '__main__':
    df = check_address("1 Apple Way")
    print(df)
    # price = get_price(link)
    # print(f"Resteraunt: {df.iloc[0]['Name']}")
    # print(f"Price: {price}")