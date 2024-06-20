import pandas as pd
from datetime import date
from selenium import webdriver
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

def webscrape_airlines():
    # Initialize the CSV
    webscrapped_flights = pd.DataFrame(columns=[
        "airline_name", "departure_city", "departure_time", "arrival_city",
        "arrival_time", "layover", "flight_date", "timestamp", "price"
    ])
    today_date = date.today()
    driver = webdriver.Chrome(ChromeDriverManager().install())

    # Function to extract flight details
    def extract_flight_details(day, month, year, flight_type):
        driver.get(
            f"https://www.makemytrip.com/flight/search?itinerary=DEL-BLR-{year}-{month:02d}-{day:02d}_BLR-DEL-{year}-{month:02d}-{day+1:02d}&tripType=R&paxType=A-1_C-0_I-0&intl=false&cabinClass=E&ccde=IN&lang=eng"
        )

        time.sleep(10)  # Wait for the page to load

        try:
            flights = driver.find_elements(By.CLASS_NAME, 'splitViewListing')
            for flight in flights:
                # Extract airline name
                airline_element = flight.find_element(By.CSS_SELECTOR, '.airline-info-wrapper + span')
                airline_name = airline_element.text.strip()

                # Extract departure time
                departure_time_element = flight.find_element(By.CSS_SELECTOR, '.timeInfoleft .flightTimeInfo span')
                departure_time = departure_time_element.text.strip()

                # Extract departure city
                departure_city_element = flight.find_element(By.CSS_SELECTOR, '.timeInfoleft .blackText font')
                departure_city = departure_city_element.text.strip()

                # Extract arrival time
                arrival_time_element = flight.find_element(By.CSS_SELECTOR, '.timeInfoRight .flightTimeInfo span')
                arrival_time = arrival_time_element.text.strip()

                # Extract arrival city
                arrival_city_element = flight.find_element(By.CSS_SELECTOR, '.timeInfoRight .blackText font')
                arrival_city = arrival_city_element.text.strip()

                # Extract layover/non-stop info
                layover_info_element = flight.find_element(By.CLASS_NAME, 'flightsLayoverInfo')
                layover_info = layover_info_element.text.strip()

                # Extract price
                price_element = flight.find_element(By.CSS_SELECTOR, '.priceInfo .blackText.fontSize16.blackFont')
                price_text = price_element.text.strip()
                price = int(price_text.replace('₹', '').replace(',', ''))

                webscrapped_flights.loc[len(webscrapped_flights)] = [
                    airline_name, departure_city, departure_time, arrival_city,
                    arrival_time, layover_info, f"{day:02d} {month:02d}", today_date, price
                ]

        except Exception as e:
            print(f"Error while scraping: {e}")

    # Scrape departure flights
    for day in range(12, 19):
        extract_flight_details(day, 6, 2024, "Departure")

    # Scrape return flights
    for day in range(13, 20):
        extract_flight_details(day, 6, 2024, "Return")

    # Calculate Total Flight Price for every date combination
    departure_df = webscrapped_flights[
        (webscrapped_flights.flight_date.str.startswith('12')) & (webscrapped_flights.timestamp == today_date)
    ]
    return_df = webscrapped_flights[
        (webscrapped_flights.flight_date.str.startswith('13')) & (webscrapped_flights.timestamp == today_date)
    ]

    for _, row_dep in departure_df.iterrows():
        for _, row_ret in return_df.iterrows():
            webscrapped_flights = webscrapped_flights.append(
                {
                    "airline_name": row_dep.airline_name,
                    "departure_city": row_dep.departure_city,
                    "departure_time": row_dep.departure_time,
                    "arrival_city": row_ret.arrival_city,
                    "arrival_time": row_ret.arrival_time,
                    "layover": row_dep.layover,
                    "flight_date": f"{row_dep.flight_date} – {row_ret.flight_date}",
                    "timestamp": today_date,
                    "price": row_dep.price + row_ret.price,
                },
                ignore_index=True,
            )

    webscrapped_flights.to_csv("webscrapped_flights.csv", index=False)

webscrape_airlines()
