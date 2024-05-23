import pymongo
import requests
import html
import re
import datetime
import argparse
from bs4 import BeautifulSoup

## Define credentials for MongoDB connection

HostName = "localhost"
MongoPort = 27017
DatabaseName = "mydatabase"

##

class Database:
    def __init__(self, db_name, host_name, mongo_port):
        self.client = pymongo.MongoClient(host_name, mongo_port)
        self.db = self.client[db_name]

    def get_collection(self, collection_name):
        return self.db[collection_name]
    
class WebScraper:
    @staticmethod
    def fetch_content(url):
        response = requests.get(url)
        return response.content
    @staticmethod
    def decode_html(html_content):
        return html.unescape(str(html_content))
    @staticmethod
    def parse_html(html_content, parser="html.parser"):
        return BeautifulSoup(html_content, parser)
    
class CollectionManager:
    def __init__(self, db):
        self.db_data = db.get_collection("Collections")
        self.get_collections_URLs()
        self.get_collections_data()
    def get_collections_URLs(self):
        url = "https://csgostash.com/containers/skin-cases"
        content = WebScraper.fetch_content(url)
        soup = WebScraper.parse_html(content)
        urls = [a['href'] for a in soup.select('a[href]') if "https://csgostash.com/case" in a['href']]
        urls = list(set(urls))  # Remove duplicates
        urls.remove("https://csgostash.com/case/292/X-Ray-P250-Package")  # Remove exception
        return urls
    
    def get_collections_data(self):
        print(f"Getting collections data\n")
        urls = self.get_collections_URLs()
        for idx,url in enumerate(urls):

            if self.db_data.find_one({"CollectionUrl": url}):
                continue
            content = WebScraper.fetch_content(url)
            decoded = WebScraper.decode_html(content)
            soup = WebScraper.parse_html(decoded)
            collection_name = soup.select_one("h1").text.strip()
            rarities = {
                "RED": len(soup.select('.quality.color-covert')),
                "Pink": len(soup.select('.quality.color-classified')),
                "Purple": len(soup.select('.quality.color-restricted')),
                "Blue": len(soup.select('.quality.color-milspec')),
                "Light-blue": len(soup.select('.quality.color-industrial')),
                "Grey": len(soup.select('.quality.color-consumer'))
            }
            collection_data = {
                "_id": collection_name,
                "Name": collection_name,
                "RedNumber": rarities["RED"],
                "PinkNumber": rarities["Pink"],
                "PurpleNumber": rarities["Purple"],
                "BlueNumber": rarities["Blue"],
                "LightBlueNumber": rarities["Light-blue"],
                "GreyNumber": rarities["Grey"],
                "CollectionUrl": url
            }

            if not self.db_data.find_one({"_id": collection_name}):
                self.db_data.insert_one(collection_data)
                print(f"Inserted collection: {collection_name}")
                inserted = 1
            if 1 == inserted and idx == len(urls) - 1:
                print("All collections exist. You can perform --update")

class SkinManager:
    def __init__(self, db, coll_manager):
        self.db_data = db.get_collection("Skins")
        self.collection_manager = coll_manager
    def get_skins_urls(self):
        print(f"Getting skins URLs(might take some time...)\n")
        for collection in self.collection_manager.db_data.find():
            exists = 0
            content = WebScraper.fetch_content(collection["CollectionUrl"])
            decoded = WebScraper.decode_html(content)
            soup = WebScraper.parse_html(decoded)
            skins_links = set([a.get('href') for a in soup.select('a') if "https://csgostash.com/skin/" in a.get('href', '')])
            for link in skins_links:
                skin_data = {"Collection_id": collection["_id"], "URL": link}
                if not self.db_data.find_one(skin_data):
                    self.db_data.insert_one(skin_data)
                    print(f"Inserted skin URL for collection: {collection['Name']}")
                    exists = 1
            if exists:
                print(f"Skins URLs already exist for collection: {collection['Name']}")
                    
    def get_prices(self, content):
            soup = WebScraper.parse_html(content)
            res_dict = {}
            a_tags = soup.findAll('a', href=lambda href: href and 'https://steamcommunity.com/market/listings' in href)
            
            for el in a_tags:
                if not el.find_parent('td'):
                    st = el.find('span', string="StatTrak")
                    wear = st.find_next_sibling() if st else el.find('span')
                    price = wear.find_next_sibling()
                    wear_text = "ST " + wear.text if st else wear.text
                    price_text = price.text.replace(" ","").replace("€","").replace(",",".")
                    
                    try:
                        price_float = float(price_text)
                    except ValueError:
                        price_float = "No value"
                    res_dict[wear_text] = price_float
            return res_dict       
    def get_skins_data(self):
        print(f"Getting skins data\n")
        for idx, skin in enumerate(self.db_data.find()):
    
            if 'Name' in skin:
                print(f"Document number {idx+1} already exists")
            else:
                try:
                    Url = skin["URL"]
                    content = WebScraper.fetch_content(Url)
                    decoded = WebScraper.decode_html(content)
                    
                    Name = Url.split("/")[-1]
                    Max_wear = re.findall(r'title="Maximum Wear \("Worst"\)">(\d+.\d+)',decoded)[0]
                    Min_wear = re.findall(r'title="Minimum Wear \("Best"\)">(\d+.\d+)',decoded)[0]
                    Rarity = re.findall(r'<div class="quality color-(\w+)"',decoded)[0]
                    
                    prices = self.get_prices(content)
                    check_price_lambda = lambda x: prices[x] if x in prices else 'No value'
                    Skin_attr = {
                        "Name"    : Name,
                        "Min_wear": Min_wear,
                        "Max_wear": Max_wear,
                        "Rarity": Rarity,
                        #Prices 
                        "ST Factory New"    :check_price_lambda("ST Factory New"),
                        "ST Minimal Wear"   :check_price_lambda("ST Minimal Wear"),
                        "ST Field-Tested"   :check_price_lambda("ST Field-Tested"),
                        "ST Well-Worn"      :check_price_lambda("ST Well-Worn"),
                        "ST Battle-Scarred" :check_price_lambda("ST Battle-Scarred"),
                        "Factory New"       :check_price_lambda("Factory New"),
                        "Minimal Wear"      :check_price_lambda("Minimal Wear"),
                        "Field-Tested"      :check_price_lambda("Field-Tested"),
                        "Well-Worn"         :check_price_lambda("Well-Worn"),
                        "Battle-Scarred"    :check_price_lambda("Battle-Scarred")
                    }
                    
                    print(f"Updating:{idx+1} document")
                    self.db_data.update_one({'_id': skin['_id']},{'$set': Skin_attr})
                except Exception as e:
                    error_name = e.__class__.__name__
                    print(f"Error fetching prices: {error_name} at index {idx}")
    def update_skins_prices(self):

        with open("./Logs/updating_log.txt","a") as file:
            log_text = "Updating prices at: "+str(datetime.datetime.now().time())+"\n"
            file.write(log_text)
            
        for idx,skin in enumerate(self.db_data.find()):
            
            try:
                url = skin["URL"]
                content = WebScraper.fetch_content(url)
                prices = self.get_prices(content)
                check_price_lambda = lambda x: prices[x] if x in prices else 'No value'
                self.db_data.update_one(
                    {"_id":skin["_id"]},
                    {"$set": 
                    {
                        "ST Factory New"    :check_price_lambda("ST Factory New"),
                        "ST Minimal Wear"   :check_price_lambda("ST Minimal Wear"),
                        "ST Field-Tested"   :check_price_lambda("ST Field-Tested"),
                        "ST Well-Worn"      :check_price_lambda("ST Well-Worn"),
                        "ST Battle-Scarred" :check_price_lambda("ST Battle-Scarred"),
                        "Factory New"       :check_price_lambda("Factory New"),
                        "Minimal Wear"      :check_price_lambda("Minimal Wear"),
                        "Field-Tested"      :check_price_lambda("Field-Tested"),
                        "Well-Worn"         :check_price_lambda("Well-Worn"),
                        "Battle-Scarred"    :check_price_lambda("Battle-Scarred")
                    }})
                
                print(f"updating {idx+1} Name: {skin["Name"]}")
            except Exception as e:
                error_name = e.__class__.__name__
                with open("./Logs/updating_log.txt","a") as file:
                    file.write(f'Error at {error_name}+"at index {idx+1}"\n')
                print("Error occured, check log for more information")
        

def main(start, update):

    if not start and not update:
        print("No action specified. Use --start od --update.")
        return 0 
    
    db = Database(DatabaseName, HostName, MongoPort)
    collectionmanager = CollectionManager(db)
    skinmanager = SkinManager(db, collectionmanager)
    if start:
        skinmanager.get_skins_urls()
        skinmanager.get_skins_data()
    elif update:
        skinmanager.update_skins_prices()
if __name__ == '__main__':
    
    parser = argparse.ArgumentParser('Manage cs2 mongoDB')
    parser.add_argument('--start', action='store_true', help="First time use only. Creating MongoDB objects.")
    parser.add_argument('--update', action='store_true', help="Updating skins prices")

    args = parser.parse_args()
    main(args.start,args.update)


