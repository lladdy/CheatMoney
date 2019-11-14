import os
import random
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
    async def manageSupply(self):
        # Supply
        if self.supply_left < 6 and self.supply_cap != 200 \
            and self.can_afford(UnitTypeId.SUPPLYDEPOT) and not self.already_pending(UnitTypeId.SUPPLYDEPOT):
            if self.townhalls:
                hq = random.choice(self.townhalls).position
                if hq:
                    supplyposition = hq.towards(self.game_info.map_center,8).random_on_distance(random.randrange(1, 12))
                    supplyposition = await self.find_placement(UnitTypeId.SUPPLYDEPOT,supplyposition)
                    if supplyposition:
                        w = self.workers.filter(lambda x: not x.is_constructing_scv).closest_to(supplyposition)
                    if w:
                        self.worker_manager.add_builder(w)
                        self.do(w.build(UnitTypeId.SUPPLYDEPOT, supplyposition))
                        
    async def macro(self):
        await self.manageSupply()
        await self.ressources.manageWorkers()
        # await self.unitmanager.createBuilding("Barracks", 4, self.hq_location)
        
        if self.structures.filter(lambda x: x.type_id in {UnitTypeId.SUPPLYDEPOT,UnitTypeId.SUPPLYDEPOTLOWERED}).ready\
            and (self.structures(UnitTypeId.BARRACKS).amount + self.already_pending(UnitTypeId.BARRACKS)) < 5:
            if self.can_afford(UnitTypeId.BARRACKS):
                hq = random.choice(self.townhalls).position
                barracks_position = hq.towards(self.game_info.map_center,8).random_on_distance(random.randrange(1, 12))
                barracks_position = await self.find_placement(UnitTypeId.BARRACKS,barracks_position)
                if barracks_position:
                    w = self.workers.filter(lambda x: not x.is_constructing_scv).closest_to(barracks_position)
                    if w:
                        self.worker_manager.add_builder(w)
                        self.do(w.build(UnitTypeId.BARRACKS, barracks_position))

        if self.structures(UnitTypeId.BARRACKS).ready:
            await self.unitmanager.createUnit("Marine", 100)

    async def attack(self):
        if self.state.game_loop/22.4 > 180:
            for unit in self.units(sc2.UnitTypeId.MARINE).ready:
                self.do(unit.attack(self.enemy_start_locations[0]))
        else:
            for unit in self.units(sc2.UnitTypeId.MARINE).ready:
                self.do(unit.attack(self.game_info.map_center))

    async def on_unit_created(self, unit: Unit):
        if unit.type_id == UnitTypeId.SCV:
            self.worker_manager.add_miner(unit)

    async def on_step(self, iteration):
        self.iteration = iteration
        for unit in self.workers.idle:
            self.worker_manager.add_miner(unit)

        await self.worker_manager.on_step(iteration)

        # if self.iteration  == 500 *8:
        #     with open('minerals.txt', 'a') as file:
        #         file.write(os.linesep + str(self.minerals))
        #         raise 'exit'  # just crash

        await self.macro()
        await self.attack()

    async def on_start(self):
        self.client.game_step = 1
        self.hq_location = self.townhalls.ready.first.position
        await self.racecheck_self()

        self.worker_manager = WorkerManager(self, [mineral for mineral in self.mineral_field.visible])

    async def on_unit_destroyed(self, unit_tag):
        return super().on_unit_destroyed(unit_tag)


class WorkerManager:
    """ Responsible for managing the workers """

    def __init__(self, bot: CheatMoney, minerals):
        self.bot = bot
        self.mining_fields = Units(minerals, self.bot)
        self.miners = Units([], self.bot)
        self.builders = Units([], self.bot)

        for mineral in self.mining_fields:
            mineral.workers_assigned = 0

    def add_miner(self, worker: Unit):
        if worker in self.builders:
            self.builders.remove(worker)
        
        has_been_assigned = False
        for mineral in self.mining_fields.sorted_by_distance_to(worker):
            if mineral.workers_assigned == 0:
                worker.assigned_mineral = mineral
                has_been_assigned = True
                mineral.workers_assigned = 1
                break

        if not has_been_assigned:
            for mineral in self.mining_fields.sorted_by_distance_to(worker):
                if mineral.workers_assigned == 1:
                    worker.assigned_mineral = mineral
                    has_been_assigned = True
                    mineral.workers_assigned = 2
                    break
        self.miners.append(worker)

    def add_builder(self, worker: Unit):

        if worker in self.miners:
            self.mining_fields.find_by_tag(self.miners.find_by_tag(worker.tag).assigned_mineral.tag).workers_assigned -= 1        
            self.miners.remove(worker)
        self.builders.append(worker)

    async def on_step(self, iteration):
        # todo: the "step rate" (or whatever it's called) might affect the efficacy of our technique
        # todo: check to see if we can change the step rate to as often as possible
        for worker in self.miners:
            # todo: mineral walk and have workers "bump" each other

            # for some reason the work in our list doesn't get its data updated, so we need to get this one
            updated_worker = self.bot.workers.find_by_tag(worker.tag)
            if updated_worker.is_carrying_minerals:  # if worker has minerals, return to base
                updated_worker.return_resource()
            # if the worker is over a certain distance away, path to mineral patch
            # todo: tweak this distance to be optimal
            elif updated_worker.distance_to(worker.assigned_mineral.position) > 1.5:
                pos = updated_worker.position - self.bot.hq_location
                norm = preprocessing.normalize([pos], norm='l1')[0]
                self.bot.do(updated_worker.move(worker.assigned_mineral.position - Point2((norm[0], norm[1]))))
            # if the worker is in range to gather, issue a gather command
            # todo: is it possible to manually check whether the worker is within gathering range?
            else:
                self.bot.do(updated_worker.gather(worker.assigned_mineral))
