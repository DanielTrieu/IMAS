import time
from spade.agent import Agent
from spade.behaviour import OneShotBehaviour, CyclicBehaviour
from spade.message import Message
from spade.template import Template
import rasa.core.agent as rasaAgent


class MarketAgent(Agent):

   
    class UserHandler(CyclicBehaviour):
        """
        this class use to handle text message from user, tranfer it to rasa, get rasa response then set it back to user 
        and sent data to other other agent.

        """
        rasa_agent = rasaAgent.create_agent('/home/daniel/rasa/test/models/20211104-131703.tar.gz')

        async def rasabot(message):
        responses = await r_agent.handle_text(message)
        reply ="sorry no reply"
        msg_type ="text"
        for response in responses:
            for response_type, value in response.items():
                msg_type = response_type
                reply=value
        return  msg_type, reply


        async def run(self):
            
            msg_recv = await self.receive(1000000) # wait for a message for 10 seconds

            print()
            print("Receive message", msg_recv)
            print()
            # message from rasa

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
                                self.set("sell_data",msg_content)
                                await self.agent.run_selling_handler()


    class Agenthandler(CyclicBehaviour):

        """
        This class handle message from other agent. 

        """

        async def run(self):
            
            msg_recv = await self.receive(1000000) # wait for a message for 10 seconds
            

            print()
            print("Receive message", msg_recv)
            print()
            
            
            if msg_recv.get_metadata('performative')=="propose":
                
                self.set("seller", str(msg_recv.sender))
                await self.agent.run_accept_proposal()

            
            
            if msg_recv.get_metadata('performative')=="cfp":
                time.sleep(1)
                await self.agent.run_propose()
            elif msg_recv.get_metadata('performative')== "accept-proposal":
                time.sleep(1)
                await self.agent.run_confirm()
                sell_data = self.get('sell_data')
                new_quantity =  int(sell_data['quantity']) - int(msg_recv.metadata['quantity'])
                sell_data["quantity"]= str(new_quantity )
                self.set('sell_data',sell_data)
                print ('new quantity', sell_data['quantity'])

            else:
                print("no matching")

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
    
    class Confirm(OneShotBehaviour):
        async def run(self ):
            #print("confirm request")
            to_agent = self.get("to_agent")
            msg = Message(to=to_agent)    # Instantiate the message
            metadata= self.get("confirm_data")
            for key, value in metadata.items():
                msg.set_metadata(key, value)
            msg.set_metadata("performative", "confirm")  # Set the "confirm" FIPA performative
            #msg.body = "Hello World"                    # Set the message content

            await self.send(msg)
            print("confirm request sent to", to_agent )

            # stop agent from behaviour
            #await self.agent.stop()    


    
        
    async def run_propose(self):
            self.add_behaviour(self.Propose())

    async def run_confirm(self):
            self.add_behaviour(self.Confirm())
    
    async def run_selling_handler(self):
            self.add_behaviour(self.Selling_handler())

    async def setup(self):
        template = Template()
        #template.set_metadata("performative", "inform")
        self.add_behaviour(self.Handler(), template)


if __name__ == "__main__":
    Seller = SellerAgent("seller1@talk.tcoop.org", "tcoop#2021")
    Seller.set("to_agent", "buyer@talk.tcoop.org/fjfe")
    #Seller.set("sell_data",{"product":"carrot", "price":"34", "quantity":"50"})
    Seller.set("confirm_data",{"product":"carrot", "price":"34", "quantity":"20"})
    future = Seller.start()
    future.result() # wait for receiver agent to be prepared.
    print("Seller 1 running")

    while Seller.is_alive():
        try:
            time.sleep(1)
        except KeyboardInterrupt:
            Seller.stop()
            break
    print("Agents finished")
