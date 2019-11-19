import os

from sklearn import preprocessing

import sc2
from cheatmoney.ressources import Ressources
from cheatmoney.techtree import TechTree
from cheatmoney.unitmanager import UnitManager
from cheatmoney.util import Util
from sc2 import UnitTypeId
from sc2.position import Point2
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

        if self.iteration == 200 *8:
            with open('minerals.txt', 'a') as file:
                file.write(os.linesep + str(self.minerals))
                raise 'exit'  # just crash

        # await self.macro()
        # await self.attack()

    async def on_start(self):
        self.client.game_step = 1
        self.hq_location = self.townhalls.ready.first.position
        await self.racecheck_self()

        self.worker_manager = WorkerManager(self, [mineral for mineral in self.mineral_field.visible])


class WorkerManager:
    """ Responsible for managing the workers """

    GATHER_RANGE = 1.4

    def __init__(self, bot: CheatMoney, minerals):
        self.bot = bot
        self.minerals = Units(minerals, self.bot)
        self.workers = Units([], self.bot)

        for mineral in self.minerals:
            mineral.workers_assigned = 0

        print(f'PATH_UNTIL_RANGE: {self.GATHER_RANGE}')

    async def add(self, worker: Unit):
        self.workers.append(worker)

        # assign workers to each mineral patch
        # prioritize the closest minerals. maximum 2 workers per patch
        for mineral in self.minerals.sorted_by_distance_to(worker):
            if mineral.workers_assigned < 2:
                worker.assigned_mineral = mineral
                mineral.workers_assigned += 1
                break

    async def on_step(self, iteration):
        # todo: the "step rate" (or whatever it's called) might affect the efficacy of our technique
        # todo: check to see if we can change the step rate to as often as possible
        for worker in self.workers:
            # todo: mineral walk and have workers "bump" each other

            # for some reason the work in our list doesn't get its data updated, so we need to get this one
            updated_worker = self.bot.workers.find_by_tag(worker.tag)
            if updated_worker.is_carrying_minerals:  # if worker has minerals, return to base
                updated_worker.return_resource()
            # if the worker is over a certain distance away, path to mineral patch
            # todo: tweak this distance to be optimal
            elif updated_worker.distance_to(worker.assigned_mineral.position) > self.GATHER_RANGE:
                pos = updated_worker.position - self.bot.hq_location
                norm = preprocessing.normalize([pos], norm='l1')[0]
                self.bot.do(updated_worker.move(worker.assigned_mineral.position - Point2((norm[0], norm[1]))))
            # if the worker is in range to gather, issue a gather command
            # todo: is it possible to manually check whether the worker is within gathering range?
            else:
                self.bot.do(updated_worker.gather(worker.assigned_mineral))
