import time, copy
from spade.agent import Agent
from spade.behaviour import OneShotBehaviour,CyclicBehaviour
from spade.message import Message
from spade.template import Template

         

class MarketAgent(Agent):

    def add_data(self, data_store, data_id, data_add):
        data= self.get(data_store)
        data[data_id] = data_add
        self.set(data_store, data)
    
    
    
    
    class Handler(CyclicBehaviour):
        async def run(self):
           
            msg_rev = await self.receive(100000) # wait for a message for 10 seconds
            print (msg_rev) 
            if msg_rev.get_metadata('performative')=="propose":
                if msg_rev.get_metadata('inform')=="supply":
                    data_rev= copy.deepcopy(msg_rev.metadata)
                    data_rev["from"]= str(msg_rev.sender)
                    self.agent.add_data("supply_data",data_rev["inform_id"], data_rev)
                    print ("supply data store")
                    print(self.get("supply_data"))
              
                                
                
                #await self.add_behaviour(self.Accept_proposal())


    class CFP(OneShotBehaviour):
        async def run(self):
            print("Call_for_proposal running")
            seller_list= self.get("seller_list")
            for seller in seller_list:
            
                msg = Message(to=seller)    # Instantiate the message
                metadata= self.get("cfp_data")
                for key, value in metadata.items():
                    msg.set_metadata(key, value)
                msg.set_metadata("performative", "cfp")  # Set the "inform" FIPA performative
                #msg.body = "Hello World"                    # Set the message content

                await self.send(msg)
                time.sleep(1)
                print("CFP Message sent!", seller)


    class Accept_proposal(OneShotBehaviour):
        async def run(self):
            print("Accept proposal running")
            seller = self.get("seller")
            print()
            msg = Message(to=seller)    # Instantiate the message
            metadata= self.get("accept_proposal_data")
            for key, value in metadata.items():
                msg.set_metadata(key, value)
            msg.set_metadata("performative", "accept-proposal")  # Set the "inform" FIPA performative
            #msg.body = "Hello World"                    # Set the message content

            await self.send(msg)
            print("Accept proposal sent to", seller )        
    
    async def run_CFP(self):
            self.add_behaviour(self.CFP())

    async def run_accept_proposal(self):
            self.add_behaviour(self.Accept_proposal())


    async def setup(self):
        template = Template()
        #template.set_metadata("performative", "inform")
        self.add_behaviour(self.Handler(), template)
        print("Market agent started")
       
        

if __name__ == "__main__":
    
    Market = MarketAgent("market@talk.tcoop.org", "tcoop#2021")
    Market.set("supply_data", {})

    future =Market.start()
    Market.web.start(hostname="127.0.0.1", port="10000")

    future.result()
    
    while Market.is_alive():
        try:
            time.sleep(3)
            #for behav in Buyer.behaviours: print(behav )
            #print (recv_behav in Buyer.behaviours)
        except KeyboardInterrupt:
            senderagent.stop()
            break