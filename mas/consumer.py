import time
from spade.agent import Agent
from spade.behaviour import OneShotBehaviour,CyclicBehaviour
from spade.message import Message
from spade.template import Template
import rasa.core.agent as rasaAgent


rasa_agent = rasaAgent.create_agent('/home/daniel/rasa/test/models/20211107-203001.tar.gz')


class ConsumerAgent(Agent):


     async def userhandle(self,user_inform):

            if user_inform["inform"]=="demand":
                self.set("demand_data", user_inform)
                self.set ("to_agent",["market@talk.tcoop.org"])
                print(user_inform)
                
                self.add_behaviour(self.DemandQuery())

    
    class UserHandler(CyclicBehaviour):
                
        async def rasabot(message):
        
            reply ="sorry no reply"
            reply_type ="text"
        
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
                            
                            reply_type = msg_type
                            reply = msg_content

            else: await self.send("sorry no reply")

            return reply_type, reply 

              
        
        async def run(self):
            
            msg_recv = await self.receive(1000000) # wait for a message for 10 seconds

            print()
            print("Receive message user", msg_recv)
            print()
            # message from rasa

            if msg_recv.body:        
                print("Message received with content:", msg_recv.body)
                message = msg_recv.body
                sender = str(msg_recv.sender)
                print("senderid", sender)

                reply_type, reply = await rasabot(message)
                """
                receive customer data from rasa
                """
                if reply_type =="custom":
                    await userhandle(reply)
                    print(reply)


            elif msg_recv.get_metadata('performative')=="user_inform":
                user_inform = copy.deepcopy(msg_recv.metadata)
                self.agent.set('sup')
                user_inform['performative']="inform"
                print(user_inform)
                await self.agent.userhandle(user_inform)
                
      

    class BotHandler(CyclicBehaviour):
        async def run(self):
            
            msg_recv = await self.receive(1000000) # wait for a message for 10 seconds
            
            print()
            print("Receive message bot handle", msg_recv)
            print()
            
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
                print("no matching Bot handle")

      class SupplyQuery(OneShotBehaviour):
        async def run(self):

            to_agent = self.get("to_agent")
            for agent in to_agent:

                msg = Message(to=agent)    # Instantiate the message
                metadata= self.get("propose_data")

                for key, value in metadata.items():
                    msg.set_metadata(key, value)
                msg.set_metadata("performative", "propose")  # Set the "inform" FIPA performative
                #msg.body = "Hello World"                    # Set the message content

                await self.send(msg)
                print("Propose sent to", to_agent )

   

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