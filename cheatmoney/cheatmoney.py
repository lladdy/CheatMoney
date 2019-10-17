import sc2
from cheatmoney.ressources import Ressources
from cheatmoney.techtree import TechTree
from cheatmoney.unitmanager import UnitManager
from cheatmoney.util import Util
from sc2 import race_worker


class CheatMoney(sc2.BotAI):

    def __init__(self):
        super().__init__()
        self.iteration = 0
        self.unitmanager = UnitManager(self)
        self.techtree = TechTree(self)
        self.util = Util(self)
        self.ressources = Ressources(self)

        self.race_self = None
        self.hq_location = None

    def detect_race(self, query):
        for unit in self.techtree.techtree['Unit']:
            if unit['name'] == query:
                return unit['race']

    async def racecheck_self(self):
        # if not self.race_self:
        self.race_self = str(self.detect_race(self.townhalls.first.name))
        print("Playing as " + str(self.race_self))

    # Proxy 4 rax all in
    # https://lotv.spawningtool.com/build/82647/

    # 5 rax
    # https://lotv.spawningtool.com/build/29987/

    async def macro(self):
        await self.ressources.manageSupply()
        await self.ressources.manageWorkers()
        await self.unitmanager.createBuilding("Barracks", 5, self.hq_location)
        await self.unitmanager.createUnit("Marine", 100)

    async def attack(self):
        if self.army_count >= 14:
            for unit in self.units(sc2.UnitTypeId.MARINE).ready:
                self.do(unit.attack(self.enemy_start_locations[0]))

    async def on_step(self, iteration):
        self.iteration = iteration
        await self.macro()
        await self.attack()

    async def on_start(self):
        self.hq_location = self.townhalls.ready.first.position
        await self.racecheck_self()
