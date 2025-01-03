from selenium import webdriver
import base64
from io import BytesIO
from PIL import Image, ImageFilter, ImageOps, ImageDraw
import pytesseract
import cv2
import numpy as np
from selenium.webdriver.edge.service import Service
from selenium.webdriver.edge.options import Options
from webdriver_manager.microsoft import EdgeChromiumDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Specify the Tesseract executable path
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

# User credentials
username_value = "118-30669"
password_value = "Kamarkuchi@1234"

# Define mobile emulation settings
mobile_emulation = {
    "deviceMetrics": {"width": 360, "height": 640, "pixelRatio": 3.0},
    "userAgent": "Mozilla/5.0 (Linux; Android 10; Mobile; rv:91.0) Gecko/91.0 Firefox/91.0"
}

# Configure Edge options
edge_options = Options()
edge_options.add_experimental_option("mobileEmulation", mobile_emulation)

# Use WebDriverManager to handle EdgeDriver
service = Service(EdgeChromiumDriverManager().install())
driver = webdriver.Edge(service=service, options=edge_options)

try:
    # Open the website in mobile mode
    driver.get("https://ncd.mohfw.gov.in/")

    # Wait for the login button to be clickable and click it
    wait = WebDriverWait(driver, 10)  # Timeout of 10 seconds
    login_icon = wait.until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, "a.mobile-login-icon"))
    )
    login_icon.click()
    logging.info("Clicked on the login button successfully!")

    # Fill in the login form
    # Wait for the username field to be visible and enter the username
    username_field = wait.until(
        EC.visibility_of_element_located((By.ID, "username"))
    )
    username_field.send_keys(username_value)

    # Wait for the password field to be visible and enter the password
    password_field = wait.until(
        EC.visibility_of_element_located((By.ID, "password"))
    )
    password_field.send_keys(password_value)

    # Locate the CAPTCHA image
    captcha_image_element = driver.find_element(By.ID, "captcha")

    # Extract the base64-encoded string from the 'src' attribute
    captcha_src = captcha_image_element.get_attribute("src")

    # Remove the 'data:image/jpg;base64,' prefix
    captcha_base64 = captcha_src.split(",")[1]

    # Decode the base64 string into bytes
    captcha_bytes = base64.b64decode(captcha_base64)

    # Load the image from the decoded bytes
    captcha_image = Image.open(BytesIO(captcha_bytes))

    # Preprocess the image
    captcha_image = captcha_image.convert("L")  # Convert to grayscale

    # Convert to numpy array for OpenCV processing
    captcha_array = np.array(captcha_image)

    # Apply binary thresholding
    _, binary_image = cv2.threshold(captcha_array, 140, 255, cv2.THRESH_BINARY)

    # Use morphological operations to remove lines
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
    cleaned_image = cv2.morphologyEx(binary_image, cv2.MORPH_OPEN, kernel)

    # Convert back to PIL image
    preprocessed_image = Image.fromarray(cleaned_image)

    # Save the preprocessed image for debugging
    preprocessed_image.save("captcha_cleaned.png")
    logging.info("Saved the preprocessed CAPTCHA image as captcha_cleaned.png")

    # Perform OCR on the cleaned image
    captcha_text = pytesseract.image_to_string(preprocessed_image, config="--psm 7")
    captcha_text = captcha_text.strip()  # Clean up whitespace

    if captcha_text:
        logging.info(f"Extracted CAPTCHA Text: {captcha_text}")
    else:
        logging.warning("CAPTCHA text could not be extracted. It appears to be empty.")

    # Fill in the CAPTCHA field on the form
    captcha_input_field = driver.find_element(By.ID, "captchaInput")
    captcha_input_field.send_keys(captcha_text)

    # Add a button click if there is a submit button
    submit_button = wait.until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, "button[type='submit']"))
    )
    submit_button.click()
    logging.info("Form submitted successfully!")

except Exception as e:
    logging.error(f"Error during form filling: {e}")

finally:
    # Wait before closing the browser
    time.sleep(10)
    # Quit the browser
    driver.quit()
