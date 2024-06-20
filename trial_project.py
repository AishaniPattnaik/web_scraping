import time
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import pandas as pd
import schedule
import os

EMAIL_ADDRESS = 'aishanipattnaik@gmail.com'
EMAIL_PASSWORD = 'Phili241004'
TO_EMAIL_ADDRESS = 'aishanipattnaik@gmail.com'
SMTP_SERVER = 'smtp.gmail.com'
SMTP_PORT = 587

MAX_BUDGET = 5000  # Example budget in your currency

CSV_FILE = 'flight_prices.csv'

if not os.path.exists(CSV_FILE):
    df = pd.DataFrame(columns=['Date', 'Departure City', 'Arrival City', 'Flight Number', 'Airline', 'Price'])
    df.to_csv(CSV_FILE, index=False)

def send_email(subject, body):
    msg = MIMEMultipart()
    msg['From'] = EMAIL_ADDRESS
    msg['To'] = TO_EMAIL_ADDRESS
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))

    with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
        server.starttls()
        server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        text = msg.as_string()
        server.sendmail(EMAIL_ADDRESS, TO_EMAIL_ADDRESS, text)

def get_user_input():
    departure_city = input("Enter the departure city code (e.g., DEL): ").strip().upper()
    arrival_city = input("Enter the arrival city code (e.g., BLR): ").strip().upper()
    departure_start_date = input("Enter the start date for departure (YYYY-MM-DD): ")
    departure_end_date = input("Enter the end date for departure (YYYY-MM-DD): ")
    return_start_date = input("Enter the start date for return (YYYY-MM-DD): ")
    return_end_date = input("Enter the end date for return (YYYY-MM-DD): ")
    num_passengers = input("Enter the number of passengers: ")
    max_budget = input("Enter your maximum budget: ")
    return departure_city, arrival_city, departure_start_date, departure_end_date, return_start_date, return_end_date, num_passengers, int(max_budget)



def scrape_makemytrip(driver, departure_city, arrival_city, departure_date, return_date, num_passengers):
    url = f"https://www.makemytrip.com/flight/search?itinerary={departure_city}-{arrival_city}-{departure_date}_{arrival_city}-{departure_city}-{return_date}&tripType=R&paxType=A-{num_passengers}_C-0_I-0&intl=false&cabinClass=E&ccde=IN&lang=eng"
    driver.get(url)
    time.sleep(5)  # Wait for the page to load
    
    try:
        flights = driver.find_elements(By.CLASS_NAME, 'splitViewListing')  # Class name for each flight card
        flight_details = []
        
        for flight in flights:
            price_element = flight.find_element(By.CLASS_NAME, 'priceInfo')  # Class name for price container
            price_text = price_element.text.strip()  # Get the text inside price element
            
            # Extract flight number and airline from flight card
            flight_number_element = flight.find_element(By.CSS_SELECTOR, '.makeFlex.hrtlCenter.spaceBetween.app > div:first-child')
            flight_number = flight_number_element.text.strip()  # Assuming this contains flight number
            
            airline_element = flight.find_element(By.CSS_SELECTOR, '.makeFlex.hrtlCenter.spaceBetween.app > div:nth-child(2)')
            airline = airline_element.text.strip()  # Assuming this contains airline name
            
            # Extract price from the price_text
            price = int(price_text.split()[0].replace(',', '').replace('₹', ''))  # Assuming price is at the beginning of price_text
            
            flight_details.append((departure_date, departure_city, arrival_city, flight_number, airline, price))
    
    except Exception as e:
        print(f"Error while scraping: {e}")
        flight_details = []
    
    return flight_details



def check_prices():
    departure_city, arrival_city, departure_start_date, departure_end_date, return_start_date, return_end_date, num_passengers, max_budget = get_user_input()

    chrome_options = Options()
    chrome_options.add_argument("--headless")
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

    try:
        departure_dates = pd.date_range(start=departure_start_date, end=departure_end_date).strftime('%d/%m/%Y').tolist()
        return_dates = pd.date_range(start=return_start_date, end=return_end_date).strftime('%d/%m/%Y').tolist()

        for departure_date in departure_dates:
            for return_date in return_dates:
                flight_details = scrape_makemytrip(driver, departure_city, arrival_city, departure_date, return_date, num_passengers)
                df = pd.read_csv(CSV_FILE)
                for detail in flight_details:
                    new_entry = pd.DataFrame({'Date': [pd.Timestamp.now()], 'Departure City': [detail[1]], 'Arrival City': [detail[2]], 'Flight Number': [detail[3]], 'Airline': [detail[4]], 'Price': [detail[5]]})
                    df = pd.concat([df, new_entry], ignore_index=True)
                    df.to_csv(CSV_FILE, index=False)

                    if detail[5] < max_budget:
                        send_email(
                            subject=f'Price Drop Alert: {detail[1]} to {detail[2]}',
                            body=f'The price has dropped below your threshold. Current price: ₹{detail[5]} for flight {detail[3]} ({detail[4]}) on {detail[1]} to {detail[2]}'
                        )
    finally:
        driver.quit()


schedule.every(1).hour.do(check_prices)

if __name__ == '__main__':
    while True:
        schedule.run_pending()
        time.sleep(1)

