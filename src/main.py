#!/usr/bin/pypy

# ~~~~~==============   HOW TO RUN   ==============~~~~~
# 1) Configure things in CONFIGURATION section
# 2) Change permissions: chmod +x bot.py
# 3) Run in loop: while true; do ./bot.py; sleep 1; done

from __future__ import print_function

import sys
import socket
import json
import time

# ~~~~~============== CONFIGURATION  ==============~~~~~
# replace REPLACEME with your team name!
team_name="TEAMBROWS"

# ~~~~~============== NETWORKING CODE ==============~~~~~
def connect(port, exchange_hostname):
    print(f"Connect: {exchange_hostname}:{port}")
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((exchange_hostname, port))
    return s.makefile('rw', 1)

def write_to_exchange(exchange, obj):
    json.dump(obj, exchange)
    exchange.write("\n")

def read_from_exchange(exchange):
    tmp = exchange.readline()
    return json.loads(tmp)

# ~~~~~============== STATE PARSING ==============~~~~~
def parse_instruments(instruments, message_loaded):
    #instrument_names = ["BOND", "GS", "MS", "WFC", "XLF", "VALBZ", "VALE"]
    if message_loaded["type"] == "book" :

        instruments[message_loaded["symbol"]] = {
            "buy": message_loaded["buy"],
            "sell": message_loaded["sell"]
            }

def find_min_on_sell(sell_table):
    minimum = [1000000,0]
    for val in sell_table:
        minimum[0] = min(val[0],minimum[0])
        if(minimum[0] == val[0]):
            minimum[1]=val[1]
    return minimum

def find_max_on_buy(buy_table):
    maximum = [0,0]
    for val in buy_table:
        maximum[0] = max(val[0],maximum[0])
        if(maximum[0]==val[0]):
            maximum[1]=val[1]
    return maximum


def find_fair_value(instrument):
    minimum = find_min_on_sell(instrument["sell"])[0]
    maximum = find_max_on_buy(instrument["buy"])[0]
    return (minimum+maximum)/2;


def fair_value_average(history, count):
    count = max(count,1)
    return sum(history[-count:])/count

# ~~~~~============== EXCHANGE CONTACT ==============~~~~~

def buy_order(exchange,instrument,price,amount,order_id):
    write_to_exchange(exchange, {"type": "add", "order_id": order_id, "symbol":instrument,
        "dir":"BUY","size":amount,"price":price})

def sell_order(exchange,instrument,price,amount,order_id):
    write_to_exchange(exchange, {"type": "add", "order_id": order_id, "symbol":instrument,
        "dir":"SELL","size":amount,"price":price})


# ~~~~~============== Frequency and history updaters ==============~~~~~

def frequency_counter(frequency, update_ratio, exchange_says):
    if "BOND" not in frequency:
        frequency = {
        "BOND":0,
        "GS":0,
        "MS":0,
        "WFC":0,
        "XLF":0,
        "VALBZ":0,
        "VALE":0
        }
    if "BOND" not in update_ratio:
        update_ratio = {
        "BOND":200,
        "GS":800,
        "MS":800,
        "WFC":800,
        "XLF":200,
        "VALBZ":800,
        "VALE":300
        }
    if exchange_says["type"] == "book":
            frequency[exchange_says["symbol"]] += 1


def history_updater(history, exchange_says):
    history = {
        "BOND":[],
        "GS":[],
        "MS":[],
        "WFC":[],
        "XLF":[],
        "VALBZ":[],
        "VALE":[]
        }
    if exchange_says["type"] == "book":
        history[exchange_says["symbol"]].append(find_fair_value(exchange_says))




# ~~~~~============== MAIN LOOP ==============~~~~~
def main(port, exchange_hostname):
    instruments = {}
    exchange = connect(port, exchange_hostname)
    write_to_exchange(exchange, {"type": "hello", "team": team_name.upper()})
    read_from_exchange(exchange)
    bank_account = 0
    frequency,update_rate = {},{}
    history = {}
    order_history = {}
    #order_history = {}
    #write_to_exchange(exchange, {"stype": "add", "order_id": 0, "symbol":"BOND","dir":"BUY","size":10,"price":1})

    buy_bond_list = []
    sell_bound_list = []

    second_clock = time.time()



    order_id=0
    while(True):
        if len(buy_bond_list) < 5:
            buy_order(exchange, "BOND", 999-(len(buy_bond_list)//2), 1, order_id)
            buy_bond_list.append(order_id)
            order_id += 1

        if len(sell_bound_list) < 5:
            sell_order(exchange, "BOND", 1000+(len(sell_bound_list)//2), 1, order_id)
            sell_bound_list.append(order_id)
            order_id += 1

        exchange_says = read_from_exchange(exchange)

        if exchange_says["type"]=="ack" or exchange_says["type"]=="error" :
            print(f"Exchange says: {exchange_says}", file=sys.stderr)
            print(f"Bank account: {bank_account}")

            if exchange_says["order_id"] in sell_bound_list:
                print("My sell order was bought")
                sell_bound_list.remove(exchange_says["order_id"])

            if exchange_says["order_id"] in buy_bond_list:
                print("My buy order was selled")
                buy_bond_list.remove(exchange_says["order_id"])


        parse_instruments(instruments, exchange_says)
        history_updater(history, exchange_says)
        frequency_counter(frequency, update_rate, exchange_says)

        if(time.time() - second_clock > 1.0):
            second_clock = time.time()
            print(f"Bank account: {bank_account}")
        print(update_rate)
        for key, val in update_rate.items():
            print(fair_value_average(history[key],val),fair_value_average(history[key],val/5)
            if fair_value_average(history[key],val)>fair_value_average(history[key],val/5):
                order_values=find_min_on_sell(val["sell"])
                bank_account-=order_values[0]*order_values[1]
                if bank_account<-30000:
                        bank_account+=order_values[0]*order_values[1]
                else:
                    buy_order(exchange,key,order_values[0],
                        order_values[1],order_id)
                    order_id+=1

            else:
                sell_order(exchange,key,find_max_on_buy(val["buy"])[0],
                        find_max_on_buy(val["buy"])[1],order_id)
                order_id+=1

        for key, val in instruments.items():
            if key == "BOND":
                #print(find_min_on_sell(val["sell"])[0],
                #    find_max_on_buy(val["buy"])[0])
                if find_min_on_sell(val["sell"])[0]<1000 and bank_account > -20000:
                    order_values=find_min_on_sell(val["sell"])
                    bank_account-=order_values[0]*order_values[1]
                    if bank_account<-30000:
                        bank_account+=order_values[0]*order_values[1]
                    else:
                        buy_order(exchange,key,order_values[0],
                            order_values[1],order_id)
                        order_id+=1
                if find_max_on_buy(val["buy"])[0]>1000:
                    sell_order(exchange,key,find_max_on_buy(val["buy"])[0],
                        find_max_on_buy(val["buy"])[1],order_id)
                    order_id+=1
        if exchange_says["type"]=="fill":
            if exchange_says["dir"]=="BUY":
                bank_account+=exchange_says["price"]*exchange_says["size"]
    print(order_history)


if __name__ == "__main__":
    port = 25000
    exchange_hostname = "test-exch-"+team_name

    if len(sys.argv) >= 2:
        print(f"Bot args: {str(sys.argv)}", file=sys.stderr)

        if sys.argv[1] == "test":
            pass
        elif sys.argv[1] == "test_slow":
            port += 1
        elif sys.argv[1] == "prod":
            exchange_hostname = "production"
    else:
        port += 2

    main(port, exchange_hostname)
