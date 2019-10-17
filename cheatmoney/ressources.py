from sc2 import race_gas
from sc2 import race_worker
from sc2.ids.unit_typeid import UnitTypeId
from sc2.ids.ability_id import AbilityId
from sc2.constants import *
from sc2.client import *
from typing import Union
import random


class Ressources:
    def __init__(self, bot=None):
        self.bot = bot
        self.maxworkers = 0
        self.bot.neededworkers = 0
        self.assigned_harvesters = 0

    async def manageSupply(self):
        # Supply
        if self.bot.supply_left < 7 and self.bot.supply_cap != 200:
            if self.bot.townhalls:
                hq = random.choice(self.bot.townhalls).position
                if hq:
                    supplyposition = hq.random_on_distance(random.randrange(1, 12))
                    if supplyposition:
                        await self.bot.unitmanager.createSupply(supplyposition)

    async def createGas(self):
        # Gas
        supplybuildingname = self.bot.techtree.get_supplyBuilding()
        supplybuildingid = self.bot.techtree.get_id_from_name(supplybuildingname)

        if self.bot.race == Race.Zerg:
            supplybuildingcount = self.bot.units(UnitTypeId(supplybuildingid)).amount
        else:
            supplybuildingcount = self.bot.structures(UnitTypeId(supplybuildingid)).amount

        if supplybuildingcount > 0:
            if self.bot.can_afford(race_gas[self.bot.race]):
                if self.bot.townhalls.ready:
                    for hq in self.bot.townhalls.ready:
                        vgs = self.bot.vespene_geyser.closer_than(15, hq.position)
                        for vg in vgs:
                            if not self.bot.structures.filter(lambda unit: unit.type_id == race_gas[self.bot.race] and unit.distance_to(vg) < 1):
                                worker = self.bot.select_build_worker(vg.position)
                                if worker is None:
                                    break
                                if worker.tag == self.bot.scout_tag:
                                    break
                                if not self.bot.already_pending(race_gas[self.bot.race]):
                                    self.bot.do(worker.build(race_gas[self.bot.race], vg))

    async def manageWorkers(self):
        """Creates and assigns workers"""
        # Distribute idle workers
        randomhq = self.bot.townhalls.ready
        if randomhq:
            randomhqpos = randomhq.random.position
            for lazy in self.bot.workers.idle:
                if randomhqpos:
                    self.bot.do(lazy.move(randomhqpos, queue=True))
            for lazyathq in self.bot.workers.idle:
                if randomhqpos:
                    mineral = self.bot.mineral_field.closest_to(randomhqpos)
                    self.bot.do(lazyathq.gather(mineral, queue=True))
                else:
                    break

        # Assign workers to minerals
        self.assigned_harvesters = 0
        for hq in self.bot.townhalls.ready:
            self.assigned_harvesters = hq.assigned_harvesters + self.assigned_harvesters

            if hq.assigned_harvesters > hq.ideal_harvesters:
                toomuch = hq.assigned_harvesters - hq.ideal_harvesters
                harvesters = self.bot.units(race_worker[self.bot.race]).ready
                harvesters_pool = []

                harvesters_pool.extend(harvesters.random_group_of(toomuch))
                if harvesters_pool:
                    for harvester in harvesters_pool:
                        for checkhq in self.bot.townhalls.ready:
                            if checkhq.assigned_harvesters < checkhq.ideal_harvesters:
                                mineral = self.bot.mineral_field.closest_to(checkhq)
                                self.bot.do(harvester.gather(mineral))

        # Assign workers to assimilators
        if self.assigned_harvesters >= 5:
            if self.bot.gas_buildings.ready.exists:
                for gasstation in self.bot.gas_buildings:
                    workers = self.bot.units(race_worker[self.bot.race])
                    assigned = gasstation.assigned_harvesters
                    ideal = gasstation.ideal_harvesters
                    needed = ideal - assigned

                    worker_pool = []
                    for x in range(0, needed):
                        worker_pool.extend(workers.random_group_of(min(needed, len(workers))))
                        if worker_pool:
                            w = worker_pool.pop()
                            if len(w.orders) == 1 and w.orders[0].ability.id in [AbilityId.HARVEST_RETURN]:
                                self.bot.do(w.move(gasstation))
                                self.bot.do(w.return_resource(queue=True))
                            else:
                                self.bot.do(w.gather(gasstation))

        # Build Workers
        self.bot.neededworkers = 0
        workerscount = self.bot.units(race_worker[self.bot.race]).amount
        for a in self.bot.gas_buildings:
            self.bot.neededworkers = self.bot.neededworkers + a.ideal_harvesters
            self.maxworkers = self.maxworkers + 3

        for h in self.bot.townhalls.ready:
            self.bot.neededworkers = self.bot.neededworkers + h.ideal_harvesters
            self.maxworkers = self.maxworkers + 16

        if (workerscount >= self.maxworkers) or (workerscount >= self.bot.neededworkers):
            return

        # Zerg specific
        if self.bot.race_self == 'Zerg':
            larvae = self.bot.units(UnitTypeId.LARVA)
            if larvae.exists:
                if not self.bot.already_pending(race_worker[self.bot.race]) and self.bot.can_afford(race_worker[self.bot.race]):
                    self.bot.do(larvae.random.train(UnitTypeId.DRONE))
        else:
            for hq in self.bot.townhalls.ready:
                if hq.is_idle and self.bot.can_afford(race_worker[self.bot.race]):
                    self.bot.do(hq.train(race_worker[self.bot.race]))
                    return
