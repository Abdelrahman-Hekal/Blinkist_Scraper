from selenium import webdriver
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait as wait
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service as ChromeService 
from selenium.common.exceptions import StaleElementReferenceException
import undetected_chromedriver as uc
import pandas as pd
import time
import csv
import sys
import numpy as np
import re

def initialize_bot():

    # Setting up chrome driver for the bot
    chrome_options = uc.ChromeOptions()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--log-level=3')
    chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])
    # installing the chrome driver
    driver_path = ChromeDriverManager().install()
    chrome_service = ChromeService(driver_path)
    # configuring the driver
    driver = webdriver.Chrome(options=chrome_options, service=chrome_service)
    ver = int(driver.capabilities['chrome']['chromedriverVersion'].split('.')[0])
    driver.quit()
    chrome_options = uc.ChromeOptions()
    #chrome_options.add_argument('--headless')
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.88 Safari/537.36")
    chrome_options.add_argument('--log-level=3')
    chrome_options.add_argument("--enable-javascript")
    chrome_options.add_argument("--start-maximized")
    chrome_options.add_argument("--incognito")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.page_load_strategy = 'eager'
    chrome_options.add_argument("--disable-notifications")
    # disable location prompts & disable images loading
    prefs = {"profile.default_content_setting_values.geolocation": 2, "profile.managed_default_content_settings.images": 2, "profile.default_content_setting_values.cookies": 2}
    chrome_options.add_experimental_option("prefs", prefs)
    driver = uc.Chrome(version_main = ver, options=chrome_options) 
    driver.set_window_size(1920, 1080)
    driver.maximize_window()
    driver.set_page_load_timeout(300)

    return driver

def scrape_Blinkist(path):

    start = time.time()
    print('-'*75)
    print('Scraping Blinkist.com ...')
    print('-'*75)
    # initialize the web driver
    driver = initialize_bot()

    # initializing the dataframe
    data = pd.DataFrame()

    # if no books links provided then get the links
    if path == '':
        name = 'Blinkist_data.xlsx'
        # getting the books under each category
        links = []
        nbooks, npages = 0, 0
        homepages = ['https://www.blinkist.com/en/sitemap']
        for homepage in homepages:
            driver.get(homepage)           
            # scraping books urls
            sec = wait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, "section[class='sitemap__section sitemap__section--books']")))
            titles = wait(sec, 10).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "a[class='sitemap-links__link']")))
            for title in titles:
                try:
                    nbooks += 1
                    print(f'Scraping the url for title {nbooks}')
                    link = title.get_attribute('href')
                    if '/books/' not in link: continue
                    links.append(link)
                except Exception as err:
                    print('The below error occurred during the scraping from Blinkist.com, retrying ..')
                    print('-'*50)
                    print(err)
                    continue
                    
        # saving the links to a csv file
        print('-'*75)
        print('Exporting links to a csv file ....')
        with open('Blinkist_links.csv', 'w', newline='\n', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['Link'])
            for row in links:
                writer.writerow([row])

    scraped = []
    if path != '':
        df_links = pd.read_csv(path)
        name = path.split('\\')[-1][:-4]
        name = name + '_data.xlsx'
    else:
        df_links = pd.read_csv('Blinkist_links.csv')

    links = df_links['Link'].values.tolist()

    try:
        data = pd.read_excel(name)
        scraped = data['Title Link'].values.tolist()
    except:
        pass

    # scraping books details
    print('-'*75)
    print('Scraping titles Info...')
    print('-'*75)
    n = len(links)
    for i, link in enumerate(links):

        if link in scraped: continue
        try:
            driver.get(link)           
            details = {}         
            print(f'Scraping the info for book {i+1}\{n}')
            # title and title link
            title_link, title, subtitle = '', '', ''              
            try:
                title_link = link
                title = wait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "h1"))).get_attribute('textContent').strip()
                subtitle = wait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, "p[class='text-p1 m:text-p0 mb-8 text-dark-grey']"))).get_attribute('textContent').strip()
            except Exception as err:
                print(f'Warning: failed to scrape the title for title: {link}')               
                          
            details['Title'] = title
            details['Subtitle'] = subtitle
            details['Title Link'] = title_link  
            
            # Author
            author = ''
            try:
                author = wait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, "div[class='mb-4 m:mb-8 font-bold text-h5']"))).get_attribute('textContent').strip()
            except:
                pass
                    
            details['Author'] = author                    

            # other info
            rating, nratings, read_time, ideas, formats = '', '', '', '', ''
            try:
                div = wait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, "div[class='grid grid-cols-2 gap-y-4 gap-x-8 w-fit']")))
                spans = wait(div, 10).until(EC.presence_of_all_elements_located((By.TAG_NAME, "span")))
                for span in spans:
                    try:
                        text = span.get_attribute('textContent').strip()
                        if 'rating' in text and text[0] != '(':
                            rating = text.split()[0]
                            if '(' in text:
                                nratings = text.split()[1].replace('(', '')
                        elif 'rating' in text and text[0] == '(':
                            nratings = text.split()[0].replace('(', '')
                        elif 'min' in text or 'hour' in text:
                            read_time = text.split()[0]
                        elif 'idea' in text:
                            ideas = text.split()[0]
                        else:
                            formats = text
                    except:
                        pass
            except:
                pass          
                
            details['Rating'] = rating             
            details['Number of Ratings'] = nratings             
            details['Summary Time (min)'] = read_time             
            details['Key Ideas'] = ideas             
            details['Formats'] = formats             

            # categories
            cat = ''
            try:
                div = wait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, "div[class='w-full overflow-hidden']")))
                tags = wait(div, 10).until(EC.presence_of_all_elements_located((By.TAG_NAME, "a")))
                for tag in tags:
                    cat += tag.get_attribute('textContent').strip() + ', '
                cat = cat[:-2]
            except:
                pass
                    
            details['Category'] = cat            
            
            # Amazon link
            Amazon = ''
            try:
                url = wait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, "a[class='flex  cursor-pointer text-blue hover:text-blue-1']"))).get_attribute('href')
                driver.get(url)
                time.sleep(1)
                Amazon = driver.current_url
            except:
                pass
                    
            details['Amazon Link'] = Amazon
            
            # appending the output to the datafame        
            data = data.append([details.copy()])
            # saving data to csv file each 100 links
            if np.mod(i+1, 100) == 0:
                print('Outputting scraped data ...')
                data.to_excel(name, index=False)
        except:
            pass

    # optional output to excel
    data.to_excel(name, index=False)
    elapsed = round((time.time() - start)/60, 10)
    print('-'*75)
    print(f'Blinkist.com scraping process completed successfully! Elapsed time {elapsed} mins')
    print('-'*75)
    driver.quit()

    return data

if __name__ == "__main__":
    
    path = ''
    if len(sys.argv) == 2:
        path = sys.argv[1]
    data = scrape_Blinkist(path)

