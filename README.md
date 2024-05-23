

# CS2 Skins Scraper
Simple script to scrape and store skins data from https://csgostash.com/containers/skin-cases in MongoDB

## Installation
1. Make sure you got MongoDB installed :)
2. Clone the repository
    ```bash
    git clone https://github.com/Poldon29/TradeupCalculatorCS2
    ```
3. Navigate to the project directory
    ```bash
    cd TradeupCalculatorCS2
    ```
4. Install dependencies
    ```bash
    pip install -r requirements.txt
    ```
## Usage
1. First use(initializing DB structure):
     ```bash
    python CS2_skin_data_scraper.py --start
    ```
2. Updating prices
   ```bash
    python CS2_skin_data_scraper.py --update
   ```
##
## Video presentation:

https://github.com/Poldon29/TradeupCalculatorCS2/assets/98114516/3a5a3e8d-7a11-4e4f-a634-5bd0272e6db6
## Document data structure in MongoDB

| Collections | Skins |                                                                                                                
| -------- | -------- | 
| _id   | _id
| Name | Collection_id
| RedNumber | URL
| PinkNumber | Battle-Scarred
| PinkNumber | Factory New
| PurpleNumber | Field-Tested
| BlueNumber | Max_wear
| LightBlueNumber | Min_wear
| GreyNumber | Minimal Wear
| CollectionUrl | Name
| | Rarity
| |ST Battle-Scarred
| |ST Factory New
| |ST Field-Tested
| |ST Minimal Wear
| |ST Well-Worn
| |Well-Worn



This script is currently slow, but it is sufficient for testing some calculations :)
