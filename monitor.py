import configparser
import json
import time
import requests
import logging
from twilio.rest import Client
logging.getLogger().setLevel(logging.DEBUG)

"""
we can keep polling following url :
https://www.essexapartmenthomes.com/EPT_Feature/PropertyManagement/Service/GetPropertyAvailabiltyByRange/514266/2024-07-15/2024-08-10
"""


URL_SAN_FERNANDO = "https://www.essexapartmenthomes.com/EPT_Feature/PropertyManagement/Service/GetPropertyAvailabiltyByRange/514266/"

# you can change availibility dates
AVAILABILITY = "2024-07-15/2024-08-10"
FINAL_URL = URL_SAN_FERNANDO + AVAILABILITY



def read_config():
    config = configparser.ConfigParser()
    config.read('config.ini')
    twilio_account_sid = config.get("twilio", "twilio_account_sid")
    twilio_auth_token = config.get("twilio", "twilio_auth_token")
    twilio_whatsapp = config.get("twilio", "twilio_whatsapp")
    whatsapp_num_list = config.get("twilio", "whatsapp_num_list").strip().split(",")
    stripped_whatsapp_num_list = []
    for num in whatsapp_num_list:
        stripped_whatsapp_num_list.append(num.strip())


    config_values = {
        'twilio_account_sid': twilio_account_sid,
        'twilio_auth_token': twilio_auth_token,
        'twilio_whatsapp': twilio_whatsapp,
        'whatsapp_num_list': stripped_whatsapp_num_list
    }
    return config_values

CONFIG = read_config()




def notify_on_whatsapp(msg):

    client = Client(CONFIG["twilio_account_sid"], CONFIG["twilio_auth_token"])

    for n in CONFIG["whatsapp_num_list"]:

        message = client.messages.create(
        from_='whatsapp:' +CONFIG["twilio_whatsapp"],
        body=msg,
        to='whatsapp:' + n
        )

    logging.info("Message sent. sid = %s ".format(message.sid))


def monitor():

    logging.info("Polling")
    headers={
  'Accept':'*/*',
  'Accept-Language':'zh-CN,zh;q=0.9,en;q=0.8,ja;q=0.7',
  "Accept-Encoding" : "gzip, deflate, br",
  'User-Agent':"PostmanRuntime/7.32.3"}

    # parsable_data_string = requests.get(FINAL_URL, headers=headers, verify=False)
    parsable_data_string = requests.request("GET", FINAL_URL, headers=headers, verify=False).json()

    # parse to json as response returned is a json string with escape chars

    parsed_data = json.loads(parsable_data_string)

    # loop through all the floor plans

    floorplans = parsed_data["result"]["floorplans"]

    available_apartments = []
    for floorplan in floorplans:
        # 2b 2b availability


        if float(floorplan["beds"]) >= 2 and float(floorplan["baths"]) >= 2:
            if int(floorplan["available_units_count"]) > 0:
                available_apartments.append(floorplan)
                # notify on whatsapp, so add to message list
            else:
                logging.info("2 Bed 2 Bath apartments are still unavailable !")

    if (len(available_apartments) > 0) :
        logging.info("found available apartments !")
        final_msg = "Please Hurry !! \nBelow aprtments are available at San Fenando 101 : \n"
        for ap in available_apartments:
            final_msg += "Apartment type : {}, Beds : {}, Baths : {}, Min Deposit : {}, Min Rent : {}, Carpet : {}, Units Available : {}.\n".format(ap["name"], ap["beds"], ap["baths"], ap["minimum_deposit"], ap["minimum_rent"], ap["minimum_sqft"], ap["available_units_count"])
        notify_on_whatsapp(final_msg)


def run():
    logging.info("Starting 101 San Fernando Apartment monitoring")
    while True:
        monitor()
        logging.info("sleeping for 15 seconds")
        time.sleep(15)




run()
