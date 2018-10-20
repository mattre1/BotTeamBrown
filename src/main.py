#!/usr/bin/pypy

# ~~~~~==============   HOW TO RUN   ==============~~~~~
# 1) Configure things in CONFIGURATION section
# 2) Change permissions: chmod +x bot.py
# 3) Run in loop: while true; do ./bot.py; sleep 1; done

from __future__ import print_function

import time
import sys
import socket
import json

# ~~~~~============== CONFIGURATION  ==============~~~~~
# replace REPLACEME with your team name!
team_name="TEAMBROWS"

# ~~~~~============== NETWORKING CODE ==============~~~~~
def connect(port, exchange_hostname):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((exchange_hostname, port))
    return s.makefile('rw', 1)

def write_to_exchange(exchange, obj):
    json.dump(obj, exchange)
    exchange.write("\n")

def read_from_exchange(exchange):
    return json.loads(exchange.readline())

# ~~~~~============== STATE PARSING ==============~~~~~
def parse_instruments(instruments, message_loaded):
    #instrument_names = ["BOND", "GS", "MS", "WFC", "XLF", "VALBZ", "VALE"]
    if message_loaded["type"] == "book" :
        # print(f"Message: {message_loaded}", file=sys.stderr)

        instruments[message_loaded["symbol"]] = {
            "buy": message_loaded["symbol"]["buy"],
            "sell": message_loaded["symbol"]["sell"]
            }

def find_min_on_sell(sell_table):
    minimum = [1000000,0]
    for val in sell_table:
        minimum = max(val[0],minimum[0])
        if(minimum[0]==val[0]):
            minimum[1]=val[1]
    return minimum

def find_max_on_buy(buy_table):
    maximum = [0,0]
    for val in buy_table:
        maximum = min(val[0],maximum[0])
        if(maximum[0]==val[0]):
            maximum[1]=val[1]
    return maximum


def find_fair_value(instrument):
    minimum = find_min_on_sell(instrument["sell"])[0]
    maximum = find_max_on_buy(instrument["buy"])[0]
    return (minimum+maximum)/2;

# ~~~~~============== EXCHANGE CONTACT ==============~~~~~

def buy_order(exchange,instrument,price,amount,order_id):
    write_to_exchange(exchange, {"type": "add", "order_id": order_id, "symbol":instrument,
        "dir":"BUY","size":amount,"price":price})

def sell_order(exchange,instrument,price,amount,order_id):
    write_to_exchange(exchange, {"type": "add", "order_id": order_id, "symbol":instrument,
        "dir":"SELL","size":amount,"price":price})



# ~~~~~============== MAIN LOOP ==============~~~~~
def main(port, exchange_hostname):
    instruments = {}
    start_time=time.time()
    exchange = connect(port, exchange_hostname)
    write_to_exchange(exchange, {"type": "hello", "team": team_name.upper()})
    hello_from_exchange = read_from_exchange(exchange)
    #write_to_exchange(exchange, {"type": "add", "order_id": 0, "symbol":"BOND","dir":"BUY","size":10,"price":1})

    order_id=0
    while(time.time()-start_time<1):
        exchange_says = read_from_exchange(exchange)
        print("Exchange says:", exchange_says, file=sys.stderr)
        parse_instruments(instruments, exchange_says)

        for key, val in instruments.items():
            if key == "BOND":
                if find_min_on_sell(val["sell"])[0]<1000:
                    buy_order(exchange,key,find_min_on_sell(val["sell"])[0],
                        find_min_on_sell(val["sell"])[1],order_id)
                    order_id+=1
                if find_max_on_buy(val["buy"])[0]>1000:
                    sell_order(exchange,key,find_max_on_buy(val["buy"])[0],
                        find_max_on_buy(val["buy"])[1],order_id)
                    order_id+=1
    # A common mistake people make is to call write_to_exchange() > 1
    # time for every read_from_exchange() response.
    # Since many write messages generate marketdata, this will cause an
    # exponential explosion in pending messages. Please, don't do that!
    print("The exchange replied:", hello_from_exchange, file=sys.stderr)

if __name__ == "__main__":
    port = 25000
    exchange_hostname = "test-exch-"

    if len(sys.argv) >= 2:
        print(f"Bot args: {str(sys.argv)}", file=sys.stderr)

        if sys.argv[1] == "test":
            exchange_hostname += team_name
        elif sys.argv[1] == "test_slow":
            port += 1
            exchange_hostname += team_name
        elif sys.argv[1] == "prod":
            exchange_hostname += "production"
    else:
        port += 2
        exchange_hostname += team_name

    main(port, exchange_hostname)
