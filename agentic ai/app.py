import os
import re
from flask import Flask, request, jsonify
from flask_cors import CORS
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup

app = Flask(__name__)
CORS(app)  # Enable CORS

# ======= Amazon ASIN Extraction =======
def extract_asin_from_url(amazon_url):
    asin_pattern = r"(?:dp|gp/product)/([A-Z0-9]{10})"
    match = re.search(asin_pattern, amazon_url)
    if match:
        return match.group(1)
    else:
        raise ValueError("ASIN not found in the provided Amazon URL.")

# ======= Flipkart PID Extraction =======
def extract_pid_from_flipkart_url(flipkart_url):
    pid_pattern = r"(?:pid=|/itm)([A-Z0-9]+)"
    match = re.search(pid_pattern, flipkart_url)
    if match:
        return match.group(1)
    else:
        print("PID not found in the provided Flipkart URL.")
        return None

# ======= Scrape Amazon Keepa Data =======
def scrape_keepa_html(keepa_url):
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    # Change the User-Agent here to simulate another device
    chrome_options.add_argument("--user-agent=Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15A372 Safari/604.1")
    
    chromedriver_path = os.getenv('CHROMEDRIVER_PATH', 'F:\\agentic ai\\chromedriver.exe')
    if not os.path.exists(chromedriver_path):
        return {"error": f"Chromedriver not found at {chromedriver_path}"}
    
    service = Service(executable_path=chromedriver_path)
    try:
        driver = webdriver.Chrome(service=service, options=chrome_options)
        driver.get(keepa_url)
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.ID, "statsTable"))
        )
        soup = BeautifulSoup(driver.page_source, "html.parser")
        stats_table = soup.find("table", id="statsTable")
        if not stats_table:
            return {"error": "Stats table not found on Keepa page."}
        
        rows = stats_table.find_all("tr")
        lowest_price = highest_price = lowest_date = highest_date = None
        for row in rows:
            cells = row.find_all("td")
            if len(cells) > 0:
                row_label = cells[0].get_text(strip=True)
                if row_label == "Lowest":
                    lowest_price = cells[2].get_text(strip=True).split("\n")[0]
                    lowest_date = cells[2].find("span", class_="statsDate").get_text(strip=True)
                elif row_label == "Highest":
                    highest_price = cells[2].get_text(strip=True).split("\n")[0]
                    highest_date = cells[2].find("span", class_="statsDate").get_text(strip=True)
        return {
            "keepa_url": keepa_url,
            "lowest_price": f"{lowest_price} on {lowest_date}" if lowest_price else "Lowest price not found.",
            "highest_price": f"{highest_price} on {highest_date}" if highest_price else "Highest price not found."
        }
    except Exception as e:
        return {"error": str(e)}
    finally:
        driver.quit()

# ======= Scrape Flipshope Product Data =======
def scrape_flipshope_product(flipshope_url):
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--user-agent=Mozilla/5.0")
    
    chromedriver_path = os.getenv('CHROMEDRIVER_PATH', 'F:\\agentic ai\\chromedriver.exe')
    if not os.path.exists(chromedriver_path):
        return {"error": f"Chromedriver not found at {chromedriver_path}"}

    service = Service(executable_path=chromedriver_path)
    try:
        driver = webdriver.Chrome(service=service, options=chrome_options)
        driver.get(flipshope_url)
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.CLASS_NAME, "statsContainer"))
        )
        soup = BeautifulSoup(driver.page_source, "html.parser")
        product_title_element = soup.find("h1", class_="productTitle")
        product_title = product_title_element.get_text(strip=True) if product_title_element else "Product title not found."

        stats_container = soup.find("div", class_="statsContainer")
        if not stats_container:
            return {"error": "Stats container not found."}

        highest_price = stats_container.find("p", class_="text-[#C53737]")
        average_price = stats_container.find("p", class_="text-[#A0C537]")
        lowest_price = stats_container.find("p", class_="text-[#00AD07]")

        return {
            "flipshope_url": flipshope_url,
            "highest_price": highest_price.get_text(strip=True) if highest_price else "Highest price not found.",
            "average_price": average_price.get_text(strip=True) if average_price else "Average price not found.",
            "lowest_price": lowest_price.get_text(strip=True) if lowest_price else "Lowest price not found."
        }
    except Exception as e:
        return {"error": str(e)}
    finally:
        driver.quit()

# ======= Amazon Scrape Route =======
@app.route('/scrape', methods=['POST'])
def scrape_amazon():
    data = request.json
    amazon_url = data.get('amazon_url')
    if not amazon_url:
        return jsonify({"error": "Amazon URL is required"}), 400
    try:
        asin = extract_asin_from_url(amazon_url)
        keepa_url = f"https://keepa.com/#!product/10-{asin}"
        result = scrape_keepa_html(keepa_url)
        if "error" in result:
            return jsonify(result), 500
        return jsonify(result), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

# ======= Flipkart Scrape Route =======
@app.route('/scrapeFlipkart', methods=['POST'])
def scrape_flipkart():
    data = request.json
    flipkart_url = data.get('flipkart_url')
    if not flipkart_url:
        return jsonify({"error": "Flipkart URL is required"}), 400
    pid = extract_pid_from_flipkart_url(flipkart_url)
    if not pid:
        return jsonify({"error": "Invalid Flipkart URL or PID not found."}), 400
    flipshope_url = f"https://flipshope.com/products/{pid}/1/pp"
    result = scrape_flipshope_product(flipshope_url)
    if "error" in result:
        return jsonify(result), 500
    return jsonify(result), 200

if __name__ == '__main__':
    app.run(debug=True)