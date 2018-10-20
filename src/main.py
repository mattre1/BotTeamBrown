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


# ~~~~~============== MAIN LOOP ==============~~~~~

def main(port, exchange_hostname):
    start_time=time.time()
    exchange = connect(port, exchange_hostname)
    write_to_exchange(exchange, {"type": "hello", "team": team_name.upper()})
    hello_from_exchange = read_from_exchange(exchange)
    write_to_exchange(exchange, {"type": "add", "order_id": 0, "symbol":"BOND","dir":"BUY","size":10,"price":1})

    while(time.time()-start_time<1):
        print("Exchange says:", read_from_exchange(exchange), file=sys.stderr)
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
