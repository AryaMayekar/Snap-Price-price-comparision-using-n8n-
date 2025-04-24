# Snap Price bot

Snap Price bot is a telegram bot which lets users chat with a Groq AI agent to clarify exactly which product they want, then automatically searches Amazon and Flipkart via an n8n workflow so you can compare live prices side-by-side. It also includes a Python script to fetch historical price data for deeper insight.

#Instructions

1. Fetch historical prices
   - Download ChromeDriver .  
   - Run the Python scraper:  
     ```bash
     python app.py
     ```  
   - In a second terminal, expose it via ngrok:  
     ```bash
     ngrok http 5000
     ```  
   - Copy the generated https:// URL and paste it into the final HTTP Request nodes of the n8n workflow (also dont forgot to add /scrape for amazon and /scrapeFlipkart for flipkart at the end of the url).
   - Also make sure to change the serp api keys in the first HTTP Request nodes(add your own key, mine got exhausted)

2. Import the n8n workflow  
   - Go to your n8n web editor (e.g. n8n.cloud).  
   - Select Workflows > Import from File.  
   - Choose the `n8n price comparison.json` file from the repo.  
   - Activate or execute the workflow to start comparing prices.
