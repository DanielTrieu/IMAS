import time
from spade.agent import Agent
from spade.behaviour import OneShotBehaviour, CyclicBehaviour
from spade.message import Message
from spade.template import Template
import asyncio

class UserAgent(Agent):

    class MessageHandler(CyclicBehaviour):
                       
        async def run(self):
            
            msg_recv = await self.receive(1000000) # wait for a message for 10 seconds
            self.set("msg_recv ", msg_recv)
            print("Receive message", msg_recv)
    
    class MessageSend(OneShotBehaviour):
        async def run(self ):
            to_agent = self.get("to_agent")
        
            msg = Message(to=to_agent)    # Instantiate the message
            metadata = self.get("message_data")
            for key, value in metadata.items():
                msg.set_metadata(key, value)

            await self.send(msg)
            print("Propose sent to", msg )
    
    
    async def send_message(self):
        self.add_behaviour(self.MessageSend())
    
    async def setup(self):
        template = Template()
        self.add_behaviour(self.MessageHandler(), template)
    
       


if __name__ == "__main__":


    ufarmer1 = UserAgent("ufarmer1@talk.tcoop.org", "tcoop#2021")
    ufarmer1.set("to_agent", "farmer1@talk.tcoop.org")
  
    future = ufarmer1.start()
    ufarmer1.set("message_data", {"performative":"user_inform", "inform":"supply", "name": "daniel","product":"carrot", "price":"34", "quantity":"500", "time_current":"1","time_min":"15","time_max":"18"})
    asyncio.run(ufarmer1.send_message())
    time.sleep(2)
    ufarmer1.set("message_data", {"performative":"user_inform", "inform":"supply", "name": "daniel","product":"carrot", "price":"34", "quantity":"600", "time_current":"2","time_min":"18","time_max":"18"})
    asyncio.run(ufarmer1.send_message())



    future.result() # wait for receiver agent to be prepared.
    print("ufarmer1 running")



    while ufarmer1.is_alive():
        try:
            time.sleep(1)
        except KeyboardInterrupt:
            ufarmer1.stop()
            break
    print("Agents finished")