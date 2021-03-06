import time, copy
from spade.agent import Agent
from spade.behaviour import OneShotBehaviour, CyclicBehaviour
from spade.message import Message
from spade.template import Template
#import rasa.core.agent as rasaAgent

#rasa_agent = rasaAgent.create_agent('/home/daniel/rasa/test/models/20211104-131703.tar.gz')

class FarmerAgent(Agent):
    
    
    def add_data(self, data_store, data_id, data_add):
        data= self.get(data_store)
        data[data_id] = data_add
        self.set(data_store, data)
    
       

    
    
    async def userhandle(self,user_inform):

            if user_inform["inform"]=="supply":
                inform_id=  user_inform["name"] + "-" + user_inform["product"] + "-" + user_inform["time_current"]
                user_inform["inform_id"]= inform_id
                self.add_data("supply_data",inform_id, user_inform)
                self.set("propose_data", user_inform)
                self.set ("to_agent",["market@talk.tcoop.org"])
                print(user_inform)
                print ("supply data store")
                print(self.get("supply_data"))
                self.add_behaviour(self.Propose())

    
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

  
    
    
    class Propose(OneShotBehaviour):
        async def run(self ):
            #print("Propose running")
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

            # stop agent from behaviour
            #await self.agent.stop()

    
    
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




    
    
    async def setup(self):
        usertemplate = Template()
        bottemplate = Template()
       
        usertemplate.set_metadata("performative", "user_inform")
        self.add_behaviour(self.UserHandler(), usertemplate)
        self.add_behaviour(self.BotHandler(), bottemplate)
        
        


if __name__ == "__main__":
    Farmer = FarmerAgent("farmer1@talk.tcoop.org", "tcoop#2021")
    Farmer.set("supply_data", {})
    #Farmer.set("to_agent", "buyer@talk.tcoop.org/fjfe")
    #Seller.set("sell_data",{"product":"carrot", "price":"34", "quantity":"50"})
    #Farmer.set("confirm_data",{"product":"carrot", "price":"34", "quantity":"20"})
    Farmer.set("id", "0")
    future = Farmer.start()
    future.result() # wait for receiver agent to be prepared.
    print("Farmer 1 running")

    while Farmer.is_alive():
        try:
            time.sleep(1)
        except KeyboardInterrupt:
            Farmer.stop()
            break
    print("Agents finished")