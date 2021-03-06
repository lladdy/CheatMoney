import math
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
    MINERAL_POP_RANGE_MAX = 0.2
    MINERAL_POP_RANGE_MIN = 0.001

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

                # if there is already a worker assigned to this patch, assign our worker partners
                if mineral.workers_assigned == 1:
                    for worker_partner in self.workers:
                        if hasattr(worker_partner, 'assigned_mineral') and worker_partner.assigned_mineral == mineral:
                            worker.worker_partner = worker_partner
                            worker_partner.worker_partner = worker

                worker.assigned_mineral = mineral
                mineral.workers_assigned += 1
                break

    async def on_step(self, iteration):
        for worker in self.workers:
            # for some reason the work in our list doesn't get its data updated, so we need to get this one
            updated_worker = self.bot.workers.find_by_tag(worker.tag)
            if updated_worker.is_carrying_minerals:  # if worker has minerals, return to base
                # check for mineral popping opportunity
                if hasattr(worker, 'worker_partner') \
                    and self.in_mineral_pop_range(worker) \
                    and self.on_correct_side_of_partner(worker)\
                    and updated_worker.distance_to(self.bot.hq_location) > 4:
                    self.bot.do(updated_worker.move(self.bot.hq_location))
                else:
                    self.bot.do(updated_worker.return_resource())
            # if the worker is over a certain distance away, path to mineral patch
            elif updated_worker.distance_to(worker.assigned_mineral.position) > self.GATHER_RANGE:
                pos = updated_worker.position - self.bot.hq_location
                norm = preprocessing.normalize([pos], norm='l1')[0]
                self.bot.do(updated_worker.move(worker.assigned_mineral.position - Point2((norm[0], norm[1]))))
            # if the worker is in range to gather, issue a gather command
            else:
                self.bot.do(updated_worker.gather(worker.assigned_mineral))

    def in_mineral_pop_range(self, worker):
        # for some reason the work in our list doesn't get its data updated, so we need to get this one
        updated_worker = self.bot.workers.find_by_tag(worker.tag)
        updated_worker_partner = self.bot.workers.find_by_tag(worker.worker_partner.tag)
        pos = updated_worker.position - updated_worker_partner.position
        range = math.hypot(pos[0], pos[1])
        return range < self.MINERAL_POP_RANGE_MAX and range > self.MINERAL_POP_RANGE_MIN

    def on_correct_side_of_partner(self, worker):
        # for some reason the work in our list doesn't get its data updated, so we need to get this one
        updated_worker = self.bot.workers.find_by_tag(worker.tag)
        updated_worker_partner = self.bot.workers.find_by_tag(worker.worker_partner.tag)
        return updated_worker_partner.distance_to(worker.assigned_mineral.position) < updated_worker.distance_to(
            worker.assigned_mineral.position)
