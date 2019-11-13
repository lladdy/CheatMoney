import os

import sc2
from cheatmoney.ressources import Ressources
from cheatmoney.techtree import TechTree
from cheatmoney.unitmanager import UnitManager
from cheatmoney.util import Util
from sc2 import UnitTypeId
from sc2.unit import Unit
from sc2.units import Units


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

    async def on_unit_created(self, unit: Unit):
        if unit.type_id == UnitTypeId.SCV:
            await self.worker_manager.add(unit)

    async def on_step(self, iteration):
        self.iteration = iteration

        await self.worker_manager.on_step(iteration)

        if self.iteration == 500:
            with open('minerals.txt', 'a') as file:
                file.write(os.linesep + str(self.minerals))
                raise 'exit'  # just crash

        # await self.macro()
        # await self.attack()

    async def on_start(self):
        self.hq_location = self.townhalls.ready.first.position
        await self.racecheck_self()

        self.worker_manager = WorkerManager(self, [mineral for mineral in self.mineral_field.visible])


class WorkerManager:
    def __init__(self, bot: CheatMoney, minerals):
        self.bot = bot
        self.minerals = Units(minerals, self.bot)
        self.workers = Units([], self.bot)

        for mineral in self.minerals:
            mineral.workers_assigned = 0

    async def add(self, worker: Unit):
        self.workers.append(worker)
        has_been_assigned = False
        for mineral in self.minerals.sorted_by_distance_to(worker):
            if mineral.workers_assigned == 0:
                worker.assigned_mineral = mineral
                has_been_assigned = True
                mineral.workers_assigned = 1
                break

        if not has_been_assigned:
            for mineral in self.minerals.sorted_by_distance_to(worker):
                if mineral.workers_assigned == 1:
                    worker.assigned_mineral = mineral
                    has_been_assigned = True
                    mineral.workers_assigned = 2
                    break

    async def on_step(self, iteration):
        for worker in self.workers:
            # for some reason the workers in the list don't update their state, so just doing this as a hack
            real_worker = self.bot.workers.find_by_tag(worker.tag)
            if real_worker.is_carrying_minerals:  # if worker has minerals, issue a return to base command
                real_worker.return_resource()
            else:  # if work doesn't have minerals, path to mineral patch
                self.bot.do(real_worker.gather(worker.assigned_mineral))
