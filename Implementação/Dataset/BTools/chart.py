from BTools.BTRequests import requester
from BTools.BTime import *
from BTools.BThreads import bThread
from math import ceil

#List of stable coins or fiat currencies listed on Binance
STABLE = [
    'USDT', 'BUSD', 'USDC', 'TUSD', 'DAI', 'IDRT', 'UAH', 'RUB', 'EUR', 'NGN', 'GBP', 'TRY', 'ZAR', 'AUD', 'BRL', 'MXN', 'CAD', 'JPY', 'INR', 'KRW', 'CNY', 'RUB', 'TRY', 'UAH'
    ]

#Request a complete exchange info from Binance
def getExchangeInfo():
    url = "exchangeInfo"
    req = requester()
    req = req.get(url)
    return req.json()

def getCandlestick(start, end, pair, interval,ctr,debug = False, request="multithreaded", poolSize = 5):
    """
    ### Request candle data from pair
    
    #### startime TIMESTAMP
    #### Endtime TIMESTAMP
    #### pair
    #### interval "15m, 1h"
    #### volume selector (0 base 1 quote)
    #### debug (optional) set to True to print debug messages
    
    ### returns open time, close time, close price, base/quote volume, and trades
    """
    
    # Cheking time interity
    if start > now() - 600000:
        raise Exception("The start time is in the future")
    if start >= end:
        raise Exception("The start time is greater than the end time")
    
    # Getting requests chunks
    limit = (end - start) / getTime(interval)
    

    if debug:
        print(f"Total candles: {limit}")
        # Getting total chunks
        chunks = limit / 1000
        print(f"Total chunks: {ceil(chunks)}")
        if request == "sequential":
            print("Request mode: sequential (you can use multithreading for better performance)")
    route = []
    
    while limit > 0:
        if limit > 1000:
            aux = 1000
        else:
            aux = limit
        # Getting the request
        route.append(f"klines?symbol={pair}&interval={interval}&startTime={start}&limit={int(aux)}")
        # Updating the start time
        start += 1000 * getTime(interval)
        limit -= 1000
    
    req = requester()
    
    if request == "multithreaded":
        response = req.multiGet(route)
        candles = []
        for i in response:
            i = i.json()
            for j in i:
                if ctr == 0:
                    #returns open time, close time, close price, base volume, and trades
                    candles.append([int(j[0]), int(j[6]), float(j[4]), float(j[5]), int(j[8])])
                else:
                    #returns open time, close time, close, quote volume and trades
                    candles.append([int(j[0]), int(j[6]), float(j[4]), float(j[7]), int(j[8])])
        return candles
    elif request == "sequential":
        response = []
        for i in route:
            i = req.get(i)
            i = i.json()
            for j in i:
                if ctr == 0:
                    #returns open time, close time, close price, base volume, and trades
                    response.append([int(j[0]), int(j[6]), float(j[4]), float(j[5]), int(j[8])])
                else:
                    #returns open time, close time, close, quote volume and trades
                    response.append([int(j[0]), int(j[6]), float(j[4]), float(j[7]), int(j[8])])
        return response 
    
    elif request == "pool":
        response = req.poolGet(route, poolSize)
        candles = []
        for i in response:
            i = i.json()
            for j in i:
                if ctr == 0:
                    #returns open time, close time, close price, base volume, and trades
                    candles.append([int(j[0]), int(j[6]), float(j[4]), float(j[5]), int(j[8])])
                else:
                    #returns open time, close time, close, quote volume and trades
                    candles.append([int(j[0]), int(j[6]), float(j[4]), float(j[7]), int(j[8])])
        return candles  
    
    else:
        raise Exception("Invalid request mode")

class pair():
    """ Pair class to handle pairs of coins"""
    def __init__(self,base: str,quote: str):
        self.base = base
        self.quote = quote
    
    def __str__(self):
        return self.base + self.quote

    def isSafe(self):
        if self.base in STABLE or self.quote in STABLE:
            return True
        else:
            return False
    
    def existsOnTime(self,time):
        """Return true if the pair exists on the given time"""
        temp = getCandlestick(time, self, "1m", 1, 0)
        if temp == []:
            return False
        else:
            if temp[0][0] < time + 60000:
                return True
            else:
                return False
    
    def getBase(self):
        """Return the base coin"""
        return self.base
    
    def getQuote(self):
        """Return the quote coin"""
        return self.quote
    
    

class pairs():
    def get(self,coin: str, timeStart = 0, timeEnd = -1):
        """
        ### Get all pairs with a given coin
        
        #### coin: str, coin to be searched
        
        #### timeStart: int, timestamp in milliseconds to check if the pair exists on the given time (now = 0)
        
        #### timeEnd: int, timestamp in milliseconds to check if the pair exists on the given time (no check = -1)
        """
        req = getExchangeInfo()
        self.pList = []
        for i in req['symbols']:
            if i['baseAsset'] == coin:
                self.pList.append(pair(i['baseAsset'],i['quoteAsset']))
            elif i['quoteAsset'] == coin:
                self.pList.append(pair(i['baseAsset'],i['quoteAsset']))
        
        #verify if the pair exists in determined time
        if timeStart == 0:
            timeStart = now() - 600000
        
        #verify if the pair exists on starting time
        self.checkList(timeStart)
        
        #Handling timeEnd
        if timeEnd != -1:
            if timeEnd < timeStart and timeEnd != 0:
                raise Exception("timeEnd must be greater than timeStart")
            
            elif timeEnd > now() - 600000:
                raise Exception("timeEnd must be less than now")
            
            elif timeEnd == 0:
                timeEnd = now() - 600000
                self.checkList(timeEnd)   
            
            else:
                self.checkList(timeEnd)
                                                      
                    
        return self.pList
    
    def checkList(self,time: int):
        threadList = []
        responses = []
        for i in self.pList:
            #Creating a thread for each request
            threadList.append(bThread(target = i.existsOnTime, args=(time,)))
        
        for i in threadList:
            #Starting all threads
            i.start()
            
        for i in threadList:
            #Waiting for all threads to finish and saving the response
            responses.append(i.join())
        
        j = 0
        for i in responses:
            if i == False:
                del self.pList[j]
                j -= 1
            j += 1 