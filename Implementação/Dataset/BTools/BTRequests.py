"""
     API tools for projects based on the Binance exchange.
     Author: Mickael de Oliveira
     Version: 1.0
"""
from BTools.BTime import *
import requests
from BTools.BThreads import bThread
from concurrent.futures import ThreadPoolExecutor

class requester():
    """
        ### Custom request class to handle erros and control spam rate
        
        #### Usage: get(route) for a get request
        
        #### multiGet(routeList) for requests running in parallel
        
        #### Be careful when using multhreading, this class is not thread safe
    """
    def get(self,route: str):
        controller = True
        while controller:
            """Send a get request for a determined route"""
            try:
                req = requests.get("https://api.binance.com/api/v3/" + route)
                #Verifying the status code on return response
                if req.status_code == 429:
                    print("too many requests, waiting for binance to unban us")
                    pause()
                elif req.status_code == 200:
                    controller = False
                else:
                    print("Error when requesting: ", req.status_code)
                    print(req.text)
            except Exception as exc:
                print("Error when requesting: ", exc)
        
        #print(req)
        return req
    
    def multiGet(self,routeList: list):
        """Send a list of get requests in parallel"""
        threadList = []
        for i in routeList:
            #Creating a thread for each request
            threadList.append(bThread(target = self.get, args = (i,)))
            threadList[-1].start()
        
        
        responses = []
        #Waiting for all threads to finish
        for i in threadList:
            responses.append(i.join())

        return responses
    
    def poolGet(self,routeList: list, poolSize: int):
        """Send a list of get requests in parallel with a pool of threads with current futures"""
        with ThreadPoolExecutor(max_workers=poolSize, thread_name_prefix='mik') as executor:
            responses = executor.map(self.get, routeList)
        
        return responses