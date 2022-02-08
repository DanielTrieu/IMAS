import asyncio
import getpass

from spade import quit_spade
from spade.agent import Agent
from spade.behaviour import OneShotBehaviour


class DummyAgent(Agent):
    class LongBehav(OneShotBehaviour):
        async def run(self):
            await asyncio.sleep(5)
            print("Long Behaviour has finished")

    class WaitingBehav(OneShotBehaviour):
        async def run(self):
            await self.agent.behav.join()  # this join must be awaited
            print("Waiting Behaviour has finished")

    async def setup(self):
        print("Agent starting . . .")
        self.behav1 = self.LongBehav()
        self.add_behaviour(self.behav1)
        self.behav2 = self.WaitingBehav()
        self.add_behaviour(self.behav2)


if __name__ == "__main__":

    dummy = DummyAgent("daniel@talk.tcoop.org", "tcoop#2021")
    future = dummy.start()
    future.result()

    dummy.behav2.join()  # this join must not be awaited

    print("Stopping agent.")
    dummy.stop()

    quit_spade()
