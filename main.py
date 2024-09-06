import os
import requests
from urllib.parse import urljoin
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, ElementClickInterceptedException, ElementNotVisibleException
from rich import print
import time
import shutil
import re

dir_name = "images"

# List of possible selectors for cookie accept buttons
possible_selectors = [
    (By.ID, "accept-cookies"),
    (By.CLASS_NAME, "cookie-consent-accept"),
    (By.XPATH, "//button[contains(text(), 'Accept')]"),
    (By.XPATH, "//button[contains(text(), 'Allow')]"),
    (By.XPATH, "//button[contains(text(), 'I accept')]"),
    (By.XPATH, "//a[contains(text(), 'Accept')]"),
    (By.XPATH, "//a[contains(text(), 'Allow')]"),
    (By.XPATH, "//button[contains(@class, 'accept')]"),
    (By.XPATH, "//button[contains(@id, 'accept')]"),
]

def accept_cookies(driver):
    for by, value in possible_selectors:
        print('selector: ', value)
        try:
            WebDriverWait(driver, 10).until(EC.element_to_be_clickable((by, value))).click()
            print("Cookies accepted using:", by, value)
            return
        except (NoSuchElementException, ElementClickInterceptedException, ElementNotVisibleException, Exception):
            continue  # Try the next selector if this one fails

    print("No cookie consent button found")

try:

    if os.path.isdir(dir_name):
        shutil.rmtree(dir_name)

    # Set up options for Chrome (headless or visible)
    chrome_options = Options()
    # chrome_options.add_argument('--headless')  # headless mode

    # Initialize the webdriver (using Chrome in this case)
    driver = webdriver.Chrome(options=chrome_options)

    # Open the webpage
    url = input("Enter the URL of the website you want to clone")
    driver.get(url)
    print("Site opened. Sleeping for a bit for it to load.")

    time.sleep(3)
    accept_cookies(driver)
    time.sleep(3)

    # Step 1: Extract the HTML content
    html_content = driver.execute_script("return document.documentElement.outerHTML;")

    # Step 2: Extract applied CSS
    css_styles = driver.execute_script("""
        var css = '';
        for (var i = 0; i < document.styleSheets.length; i++) {
            try {
                var rules = document.styleSheets[i].cssRules;
                if (rules) {
                    for (var j = 0; j < rules.length; j++) {
                        css += rules[j].cssText + '\\n';
                    }
                }
            } catch (e) {
                console.log('Access to stylesheet %s is denied. Error: %s', document.styleSheets[i].href, e);
            }
        }
        return css;
    """)

    if not os.path.exists('images'):
        os.makedirs('images')

    image_map = {}

    # Find all image elements
    try:
        image_elements = driver.find_elements(By.TAG_NAME, 'img')
    except NoSuchElementException as ex:
        print("<img> not found in DOM tree.")
    
    for index, img in enumerate(image_elements):
        img_url = img.get_attribute('src') # or img.get_attribute('data-src') or img.get_attribute('data-lazy') or img.get_attribute('srcset')
        
        # Convert relative URLs to absolute
        img_url = urljoin(url, img_url)

        if img_url.startswith("data:"):
            continue
        
        try:
            img_data = requests.get(img_url).content
            img_name = f'image_{index}.png'
            img_path = os.path.join(dir_name, img_name)
            
            # Save the image locally
            with open(img_path, 'wb') as img_file:
                img_file.write(img_data)
            
            # Record the local image path to replace in the HTML
            image_map[img_url] = os.path.join(dir_name, img_name)
        except Exception as e:
            print(f"Error downloading {img_url}: {e}")

    # Step 3.2: Find inline background images (e.g., <i> with style="background-image: url(...)")
    try:
        background_elements = driver.find_elements(By.XPATH, '//*[@style]')
    except NoSuchElementException as ex:
        print("inline <style> not found in DOM tree.")

    for element in background_elements:
        style_attr = element.get_attribute('style')
        
        # Use regex to find background-image URLs in inline styles
        bg_images = re.findall(r'background-image:\s*url\(["\']?(.*?)["\']?\)', style_attr)
        
        for index, bg_url in enumerate(bg_images):
            bg_url = urljoin(url, bg_url)

            if bg_url.startswith("data:"):
                continue
            
            try:
                # Download the background image
                img_data = requests.get(bg_url).content
                img_name = f'background_{index}.png'
                img_path = os.path.join(dir_name, img_name)
                
                # Save the image locally
                with open(img_path, 'wb') as img_file:
                    img_file.write(img_data)
                
                # Record the local path and update the inline style
                image_map[bg_url] = os.path.join(dir_name, img_name)
                html_content = html_content.replace(bg_url, image_map[bg_url])
            except Exception as e:
                print(f"Error downloading background image {bg_url}: {e}")

    # Step 3.3: Find background images in CSS
    css_bg_images = re.findall(r'background-image:\s*url\(["\']?(.*?)["\']?\)', css_styles)

    for index, bg_url in enumerate(css_bg_images):
        bg_url = urljoin(url, bg_url)

        if bg_url.startswith("data:"):
            continue
        
        try:
            img_data = requests.get(bg_url).content
            img_name = f'css_background_{index}.png'
            img_path = os.path.join(dir_name, img_name)
            
            # Save the image locally
            with open(img_path, 'wb') as img_file:
                img_file.write(img_data)
            
            # Record the local path and update the CSS
            css_styles = css_styles.replace(bg_url, os.path.join(dir_name, img_name))
        except Exception as e:
            print(f"Error downloading background image from CSS {bg_url}: {e}")
    
    print(image_map)

    # Step 4: Replace image URLs in the HTML content
    for img_url, local_path in image_map.items():
        if img_url.startswith(('http:', 'https:')):
            html_content = html_content.replace(img_url, local_path)
    
    print("Styles parsed")

    # Step 5: Combine HTML and CSS
    full_page = f"<style>\n{css_styles}\n</style>\n{html_content}"

    # Step 6: Save the updated HTML content
    with open('webpage_with_styles.html', 'w', encoding='utf-8') as file:
        file.write(full_page)
    
    print("Assets saved into file.")

except Exception as ex:
    print(ex)
finally:
    # Close the driver
    driver.quit()
    print("Closed driver. Quitting gracefully.")
