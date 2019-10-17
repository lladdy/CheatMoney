from sc2.client import *
from sc2.constants import *
import random

class UnitManager():
    def __init__(self, bot=None):
        self.bot = bot

    async def trainSkill(self, skillname):
        """Builds everything required for an Abiltiy"""
        skillid = self.bot.techtree.get_id_from_name(skillname)
        trainbuilding = self.bot.techtree.get_trainBuilding(skillname)
        skillrequirements = self.bot.techtree.get_skill_buildRequirement(skillname)
        if skillrequirements:
            for requirement in skillrequirements:
                if 'building' in requirement:
                    buildingid = UnitTypeId(requirement['building'])
                elif 'addon' in requirement:
                    buildingid = UnitTypeId(requirement['addon'])
                buildingname = self.bot.techtree.get_name_from_id(buildingid.value)
                await self.createBuilding(buildingname, 1, self.bot.hq_location)

        if not self.bot.structures(trainbuilding).exists:
            buildingname = self.bot.techtree.get_name_from_id(trainbuilding.value)
            await self.createBuilding(buildingname, 1, self.bot.hq_location)
        else:
            if self.bot.can_afford(AbilityId(skillid)):
                if self.bot.structures(trainbuilding).ready:
                    tb = self.bot.structures(trainbuilding).ready.first
                    self.bot.do(tb(AbilityId(skillid)))

    async def createUnit(self, unitname, count):
        """Builds everything required to Train a Unit / Trains a Unit"""
        trainbuilding = self.bot.techtree.get_trainBuilding(unitname)
        trainunittype = self.bot.techtree.get_id_from_name(unitname)
        supplycost = self.bot.techtree.get_supplycost(unitname)
        unitcount = self.bot.units(trainunittype).amount
        unitrequirement = self.bot.techtree.get_unit_buildRequirement(unitname)

        # Build a Supply if we dont have enough for a given Unit
        if self.bot.supply_left < supplycost:
            await self.bot.ressources.manageSupply()

        if unitcount < count:
            if trainbuilding:
                if self.bot.can_afford(trainunittype):
                    # Protoss specific
                    # if self.bot.race_self == 'Protoss' and trainbuilding.name == 'GATEWAY':
                    #     if self.bot.structures(UnitTypeId.WARPGATE).ready:
                    #         if self.bot.structures(UnitTypeId.WARPGATE).ready.idle:
                    #             trainstructure = self.bot.structures(UnitTypeId.WARPGATE).ready.idle.first
                    #             abilities = await self.bot.get_available_abilities(trainstructure)
                    #             if AbilityId.WARPGATETRAIN_STALKER in abilities:
                    #                 pylon = self.bot.structures(UnitTypeId.PYLON).closest_to(trainstructure)
                    #                 pos = pylon.position.to2.random_on_distance(4)
                    #                 possible_positions = {pos + Point2((x, y)) for x in range(-5, 6) for y in range(-5, 6)}
                    #                 better_positions = pos.sort_by_distance(possible_positions)
                    #                 for placement in better_positions:
                    #                     if not self.bot.util.outofbounds(placement):
                    #                         if self.bot.in_placement_grid(placement):
                    #                             self.bot.do(trainstructure.warp_in(trainunittype, placement))
                    #                             break
                    #
                    #     else:
                    #         if self.bot.structures(trainbuilding).ready.idle:
                    #             trainstructure = self.bot.structures(trainbuilding).ready.idle.first
                    #             self.bot.do(trainstructure.train(trainunittype))

                    # elif unitname == 'Observer':
                    #     observers = self.bot.units(UnitTypeId.OBSERVER).ready
                    #     observersiege = self.bot.units(UnitTypeId.OBSERVERSIEGEMODE).ready
                    #     allobservers = observers | observersiege
                    #     if allobservers:
                    #         if allobservers.amount >= count:
                    #             return

                    # else:
                    if self.bot.structures(trainbuilding).ready.idle:
                        trainstructure = self.bot.structures(trainbuilding).ready.idle.first
                        print("Training: " + str(unitname))
                        self.bot.do(trainstructure.train(trainunittype))

                if self.bot.structures(trainbuilding).exists:
                    if unitrequirement:
                        for requirement in unitrequirement:
                            if 'building' in requirement:
                                buildingid = UnitTypeId(requirement['building'])
                            elif 'addon' in requirement:
                                buildingid = UnitTypeId(requirement['addon'])
                            buildingname = self.bot.techtree.get_name_from_id(buildingid.value)
                            await self.createBuilding(buildingname, 1, self.bot.hq_location)

                else:
                    trainbuildingid = trainbuilding.value
                    trainbuildingname = self.bot.techtree.get_name_from_id(trainbuildingid)

                    # Zerg specific
                    if trainbuildingname == "Larva":
                        unitid = self.bot.techtree.get_id_from_name(unitname)
                        larvas = self.bot.units(UnitTypeId.LARVA).ready
                        buildingname = None
                        if unitrequirement:
                            for requirement in unitrequirement:
                                if 'building' in requirement:
                                    buildingid = UnitTypeId(requirement['building'])
                                elif 'addon' in requirement:
                                    buildingid = UnitTypeId(requirement['addon'])
                                buildingname = self.bot.techtree.get_name_from_id(buildingid.value)
                                await self.createBuilding(buildingname, 1, self.bot.hq_location)

                        requirementbuildingid = self.bot.techtree.get_id_from_name(buildingname)
                        if larvas:
                            if self.bot.structures(requirementbuildingid).ready.exists:
                                if self.bot.can_afford(unitid):
                                    print("Training: " + str(unitname))
                                    self.bot.do(larvas.random.train(unitid))

                    elif trainbuildingname == "Zergling":
                        zerglings = self.bot.units(UnitTypeId.ZERGLING).ready
                        if not zerglings:
                            await self.createUnit("Zergling", 1)
                            return

                        unitid = self.bot.techtree.get_id_from_name(unitname)
                        buildingname = None
                        if unitrequirement:
                            for requirement in unitrequirement:
                                if 'building' in requirement:
                                    buildingid = UnitTypeId(requirement['building'])
                                elif 'addon' in requirement:
                                    buildingid = UnitTypeId(requirement['addon'])
                                buildingname = self.bot.techtree.get_name_from_id(buildingid.value)
                                await self.createBuilding(buildingname, 1, self.bot.hq_location)

                        requirementbuildingid = self.bot.techtree.get_id_from_name(buildingname)
                        if zerglings:
                            if self.bot.structures(requirementbuildingid).ready.exists:
                                if self.bot.can_afford(unitid):
                                    print("Training: " + str(unitname))
                                    self.bot.do(zerglings.random.train(unitid))

                    else:
                        await self.createBuilding(trainbuildingname, 1, self.bot.hq_location)

    async def createSupply(self, position, maxrange=8, force=False):
        """Creates Supply"""
        buildingname = self.bot.techtree.get_supplyBuilding()
        buildingid = self.bot.techtree.get_id_from_name(buildingname)
        building = UnitTypeId(buildingid)

        # Zerg specific
        if buildingname == 'Overlord':
            larvae = self.bot.units(UnitTypeId.LARVA)
            if larvae.exists:
                if not self.bot.already_pending(building) and self.bot.can_afford(building):
                    print("Building supply: " + str(buildingname))
                    self.bot.do(larvae.random.train(UnitTypeId.OVERLORD))
                    return

        if not self.bot.already_pending(building) and self.bot.can_afford(building):
            worker = self.bot.select_build_worker(position)
            if worker is None:
                return

            if maxrange != 0:
                supplyposition = position.random_on_distance(random.randrange(1, maxrange))
            else:
                supplyposition = position

            # supplypositionpositiondistancetoramp = supplyposition.distance_to(self.bot.ramp_location)
            # if supplypositionpositiondistancetoramp <= 7 and force == False:
            #     return

            if self.bot.util.outofbounds(supplyposition):
                return
            if not self.bot.in_placement_grid(supplyposition):
                return

            p = await self.bot.can_place(buildingid, supplyposition)
            if not p:
                return

            if self.bot.gas_buildings.exists:
                nextgas = self.bot.gas_buildings.closest_to(supplyposition)
                gas_distance2buildplace = nextgas.position.distance_to(supplyposition)
                if gas_distance2buildplace <= 7 and force is False:
                    return

            nextmineral = self.bot.resources.closest_to(supplyposition)
            distance2buildplace = nextmineral.position.distance_to(supplyposition)
            if distance2buildplace <= 7 and force is False:
                return

            print("Building supply: " + str(buildingname))
            self.bot.do(worker.build(building, supplyposition))

    async def createBuilding(self, buildingname, count, position=None, maxrange=15, force=False):
        """Builds everything required for a Building / Builds a Building"""
        if not position:
            if self.bot.townhalls:
                position = random.choice(self.bot.townhalls).position
            else:
                position = random.choice(self.bot.hq_location)

        buildingid = self.bot.techtree.get_id_from_name(buildingname)
        buildingcount = self.bot.all_units(buildingid).amount
        buildrequirement = self.bot.techtree.get_building_buildRequirement(buildingid)

        if buildingcount < count:
            if self.bot.can_afford(buildingid):
                # Zerg specific
                if buildingname == 'Lair':
                    spawningpools = self.bot.structures(UnitTypeId.SPAWNINGPOOL).ready
                    if not spawningpools:
                        await self.createBuilding("SpawningPool", 1, self.bot.hq_location)
                        return

                    hqs = self.bot.structures(UnitTypeId.HATCHERY).ready
                    if hqs:
                        hq = hqs.first
                        if hq:
                            abilities = await self.bot.get_available_abilities(hq)
                            if AbilityId.UPGRADETOLAIR_LAIR in abilities:
                                self.bot.do(hq(AbilityId.UPGRADETOLAIR_LAIR))

                elif buildingname == 'Hive':
                    if not self.bot.structures(UnitTypeId.LAIR).ready:
                        await self.createBuilding("Lair", 1, self.bot.hq_location)
                        return
                    infestationpits = self.bot.structures(UnitTypeId.INFESTATIONPIT).ready
                    if not infestationpits:
                        await self.createBuilding("InfestationPit", 1, self.bot.hq_location)
                        return
                    hqs = self.bot.structures(UnitTypeId.LAIR).ready
                    if hqs:
                        hq = hqs.first
                        if hq:
                            abilities = await self.bot.get_available_abilities(hq)
                            if AbilityId.UPGRADETOHIVE_HIVE in abilities:
                                self.bot.do(hq(AbilityId.UPGRADETOHIVE_HIVE))

                # Check if there is a Requirement
                if buildrequirement:
                    for requirement in buildrequirement:
                        requirementbuildingid = UnitTypeId(requirement['building'])

                        # Create the required Building
                        if not self.bot.structures(requirementbuildingid).exists:
                            if not self.bot.already_pending(requirementbuildingid):
                                requirementbuildingname = self.bot.techtree.get_name_from_id(requirementbuildingid.value)

                                # Zerg specific
                                if requirementbuildingname == 'Lair':
                                    spawningpools = self.bot.structures(UnitTypeId.SPAWNINGPOOL).ready
                                    if not spawningpools:
                                        await self.createBuilding("SpawningPool", 1)
                                        return

                                    hqs = self.bot.structures(UnitTypeId.HATCHERY).ready
                                    if hqs:
                                        hq = hqs.first
                                        if hq:
                                            abilities = await self.bot.get_available_abilities(hq)
                                            if AbilityId.UPGRADETOLAIR_LAIR in abilities:
                                                self.bot.do(hq(AbilityId.UPGRADETOLAIR_LAIR))

                                elif requirementbuildingname == 'Hive':
                                    infestationpits = self.bot.structures(UnitTypeId.INFESTATIONPIT).ready
                                    if not infestationpits:
                                        await self.createBuilding("InfestationPit", 1, self.bot.hq_location)
                                        return
                                    hqs = self.bot.structures(UnitTypeId.LAIR).ready
                                    if hqs:
                                        hq = hqs.first
                                        if hq:
                                            abilities = await self.bot.get_available_abilities(hq)
                                            if AbilityId.UPGRADETOHIVE_HIVE in abilities:
                                                self.bot.do(hq(AbilityId.UPGRADETOHIVE_HIVE))

                                else:
                                    if self.bot.townhalls:
                                        await self.createBuilding(requirementbuildingname, 1, random.choice(self.bot.townhalls).position, 15)
                                        return
                                    else:
                                        await self.createBuilding(requirementbuildingname, 1, self.bot.hq_location, 15)
                                        return

                morphinfo = self.bot.techtree.get_building_morphbuilding(buildingid)
                if morphinfo:
                    # Buildings that are morphed
                    (morphbuildingid, morphability) = morphinfo
                    morphbuildingtype = UnitTypeId(morphbuildingid)
                    morphabilitytype = AbilityId(morphability)
                    morphbuildings = self.bot.structures(morphbuildingtype).ready
                    if morphbuildings:
                        morphbuilding = morphbuildings[0]
                        if morphbuilding:
                            print("Morphing: " + str(buildingname))
                            self.bot.do(morphbuilding(morphabilitytype))
                            return
                else:
                    # Buildings that are build
                    # Return if there is no worker available
                    worker = self.bot.select_build_worker(position)
                    if worker is None:
                        return

                    # if worker.tag == self.bot.scout_tag:
                    #     return

                    if maxrange != 0:
                        randomposition = position.random_on_distance(random.randrange(1, maxrange))
                    else:
                        randomposition = position

                    # Protoss specific - Make sure Buildings a created around a Pylon Pos.
                    # if self.bot.race_self == 'Protoss' and force is False:
                    #     pylons = self.bot.units(UnitTypeId.PYLON).ready
                    #     if pylons:
                    #         for pylon in pylons:
                    #             for hq in self.bot.townhalls:
                    #                 # Make sure we dont build at a Proxy Pylon
                    #                 if pylon.position.distance_to(hq.position) >= 25:
                    #                     return
                    #             randomposition = pylon.position.random_on_distance(random.randrange(1, 6))

                    if self.bot.util.outofbounds(randomposition):
                        return

                    # Return if its not in placement grid
                    if not self.bot.in_placement_grid(randomposition):
                        return

                    # Return if its not in pathing grid
                    if not self.bot.in_pathing_grid(randomposition):
                        return

                    # Return if its not in placement grid
                    p = await self.bot.can_place(buildingid, randomposition)
                    if not p:
                        return

                    closebuildings = self.bot.structures.filter(lambda w: w.distance_to(randomposition) <= 3)
                    if closebuildings and force == False:
                        return

                    # Make sure its not build close to the ramp
                    # randompositiondistancetoramp = randomposition.distance_to(self.bot.ramp_location)
                    # if randompositiondistancetoramp <= 6 and force == False:
                    #     return

                    # Make sure its not build close to minerals
                    nextmineral = self.bot.mineral_field.closest_to(randomposition)
                    mineral_distance2buildplace = nextmineral.position.distance_to(randomposition)
                    if mineral_distance2buildplace <= 6:
                        return

                    # Make sure its not build close to gas
                    if self.bot.gas_buildings.exists:
                        nextgas = self.bot.gas_buildings.closest_to(randomposition)
                        gas_distance2buildplace = nextgas.position.distance_to(randomposition)
                        if gas_distance2buildplace <= 6:
                            return

                    # Protoss specific
                    # if self.bot.race_self == 'Protoss':
                    #     # Make sure Buildings a created in psyonic matrix
                    #     if not self.bot.state.psionic_matrix.covers(randomposition):
                    #         return
                    #
                    #     # Count Gateways/Warpgates
                    #     if buildingname == 'Gateway':
                    #         gatewaycount = 0
                    #         warpgatecount = 0
                    #         if self.bot.structures(UnitTypeId.GATEWAY).exists:
                    #             gatewaycount = self.bot.structures(UnitTypeId.GATEWAY).amount
                    #         if self.bot.structures(UnitTypeId.WARPGATE).exists:
                    #             warpgatecount = self.bot.structures(UnitTypeId.WARPGATE).amount
                    #         if (gatewaycount + warpgatecount) >= count:
                    #             return

                    #await self.bot._client.debug_text("B", randomposition)  # DEBUG
                    print("Building: " + str(buildingname))
                    self.bot.do(worker.build(buildingid, randomposition))
                    return
