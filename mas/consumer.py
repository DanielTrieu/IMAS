import time
from spade.agent import Agent
from spade.behaviour import OneShotBehaviour,CyclicBehaviour
from spade.message import Message
from spade.template import Template
import rasa.core.agent as rasaAgent


rasa_agent = rasaAgent.create_agent('/home/daniel/rasa/test/models/20211107-203001.tar.gz')


class BuyerAgent(Agent):
     
    class Handler(CyclicBehaviour):
        async def run(self):
           
            msg_recv = await self.receive(100000) # wait for a message for 10 seconds
      
            if msg_recv.body:
     
                print("Message received with content:", msg_recv.body)
                message = msg_recv.body
                sender = str(msg_recv.sender)
                print("senderid", sender)
                rasa_responses = await rasa_agent.handle_text(message, sender_id=sender)
                if rasa_responses:
                    
                    # rasa_responses : [{'recipient_id': 'default', 'text': 'All done!'}, {'recipient_id': 'default', 'custom': {'product': 'carrot', 'quantity': '20', 'price': '35', 'self_made_product': 'True'}}]
                    print(rasa_responses)
                    for response in rasa_responses:
                        for msg_type, msg_content in response.items():
                            if msg_type == "text":
                                #sender = str(msg_recv.sender)
                                msg_sent =Message(to=sender)
                                msg_sent.body= msg_content
                                await self.send(msg_sent)
                            if msg_type =="custom":
                                print (msg_content)
                                self.set("buy_data",msg_content)
                                await self.agent.run_CFP()
                                msg_sent =Message(to=sender)
                                msg_sent.body= "Finish set up " + str(msg_content)
                                await self.send(msg_sent)    


            
            if msg_recv.get_metadata('performative')=="propose":
                
                self.set("seller", str(msg_recv.sender))
                await self.agent.run_accept_proposal()

            if msg_recv.get_metadata('performative')=="confirm":
                to_agent ="daniel@talk.tcoop.org"
                msg = Message(to=to_agent)
                msg.body = "receive confirm from "+((str(msg_recv.sender)).split("/"))[0]+" : "+str(msg_recv.metadata)
                await self.send(msg)
                


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
        print("Buyer agent started")
       
        

if __name__ == "__main__":
    seller_list =["seller1@talk.tcoop.org", "seller2@talk.tcoop.org"]
    buy_product ={ "product":"carrot", "quantity":"12"}

    
    Buyer = BuyerAgent("buyer@talk.tcoop.org", "tcoop#2021")
    Buyer.set("seller_list",["seller1@talk.tcoop.org", "seller2@talk.tcoop.org"])
    Buyer.set("to_agent", "seller1@talk.tcoop.org/ddf")
    Buyer.set("buy_data", {"product":"carrot", "quantity":"5"})
    Buyer.set("cfp_data", {"product":"carrot", "quantity":"5"})
    Buyer.set("accept_proposal_data", {"product":"carrot", "price":"34", "quantity":"5"} )
    future =Buyer.start()
    Buyer.web.start(hostname="127.0.0.1", port="10000")

    future.result()
    
    while Buyer.is_alive():
        try:
            time.sleep(3)
            #for behav in Buyer.behaviours: print(behav )
            #print (recv_behav in Buyer.behaviours)
        except KeyboardInterrupt:
            Buyer.stop()
            break