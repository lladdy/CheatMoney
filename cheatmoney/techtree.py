import json
import random
from sc2.ids.unit_typeid import UnitTypeId
from sc2.ids.ability_id import AbilityId
from sc2.ids.upgrade_id import UpgradeId
from sc2.constants import *


class TechTree():
    def __init__(self, bot=None):
        with open('./cheatmoney/techtree.json') as techtree_json:
            self.techtree = json.load(techtree_json)

        self.bot = bot
        self.ability = self.techtree['Ability']
        self.unit = self.techtree['Unit']

        self.maxworkers = 0
        self.neededworkers = 0

    def get_id_from_name(self, name):
        for unit in self.unit:
            if unit['name'] == name:
                return UnitTypeId(unit['id'])

        for ability in self.ability:
            if ability['name'] == name:
                return ability['id']

    def get_name_from_id(self, unitid):
        for unit in self.unit:
            if unit['id'] == unitid:
                return unit['name']

        for ability in self.ability:
            if ability['id'] == unitid:
                return ability['name']


    def get_unit_buildRequirement(self, unitname):
        buildunit_creationability = self.get_trainAbillity(unitname)
        buildunit_trainbuilding = self.get_trainBuilding(unitname).value

        for unit in self.unit:
            if unit['id'] == buildunit_trainbuilding:
                for ability in unit['abilities']:
                    if ability['ability'] == buildunit_creationability:
                        if 'requirements' in ability:
                            return ability['requirements']

    def get_unit_weaponrange(self, unittype):
        unitname = self.get_name_from_id(unittype.value)
        for unit in self.unit:
            if unit['name'] == unitname:
                if 'weapons' in unit:
                    for weapon in unit['weapons']:
                        if 'range' in weapon:
                            range = weapon['range']
                            return range
                        else:
                            return 0

    def get_unit_weaponcooldown(self, unittype):
        unitname = self.get_name_from_id(unittype.value)
        for unit in self.unit:
            if unit['name'] == unitname:
                if 'weapons' in unit:
                    for weapon in unit['weapons']:
                        if 'cooldown' in weapon:
                            cooldown = weapon['cooldown']
                            return cooldown
                        else:
                            return 0

    def get_unit_attributes(self, unittype):
        unitname = self.get_name_from_id(unittype.value)
        for unit in self.unit:
            if unit['name'] == unitname:
                if 'attributes' in unit:
                    return unit['attributes']

    def can_attack(self, unit, enemyunit):
        unittype = unit.type_id
        unitname = self.get_name_from_id(unittype.value)

        target_type = None
        for unit in self.unit:
            if unit['name'] == unitname:
                if 'weapons' in unit:
                    for weapon in unit['weapons']:
                        if 'target_type' in weapon:
                            target_type = weapon['target_type']
                            if target_type == 'Ground':
                                if not enemyunit.is_flying:
                                    return 1
                                else:
                                    return 0
                            elif target_type == 'Air':
                                if enemyunit.is_flying:
                                    return 1
                                else:
                                    return 0
                            elif target_type == 'Any':
                                return 1
                        else:
                            return 0


    def get_supplycost(self, name):
        for unit in self.unit:
            if unit['name'] == name:
                return unit['supply']

    def get_building_buildRequirement(self, buildingid):
        if buildingid:
            unitname = self.get_name_from_id(buildingid.value)
            buildunit_creationability = self.get_trainAbillity(unitname)
            buildunit_trainbuilding = self.get_trainBuilding(unitname).value

            for unit in self.unit:
                if unit['id'] == buildunit_trainbuilding:
                    for ability in unit['abilities']:
                        if ability['ability'] == buildunit_creationability:
                            if 'requirements' in ability:
                                return ability['requirements']

    def get_skill_buildRequirement(self, skillname):
        if skillname:
            skillid = self.get_id_from_name(skillname)
            for unit in self.unit:
                for ability in unit['abilities']:
                    if ability['ability'] == skillid:
                        if 'requirements' in ability:
                            return ability['requirements']

    def get_building_morphbuilding(self, buildingid):
        if buildingid:
            # ORBITALCOMMAND ID = 132
            # UPGRADETOORBITAL_ORBITALCOMMAND ID = 1516
            for ability in self.ability:
                if 'Morph' in ability['target']:
                    if ability['target']['Morph']['produces'] == buildingid.value:
                        morphability = ability['id']

                        for unit in self.unit:
                            for ability in unit['abilities']:
                                if ability == morphability:
                                    return (unit['id'], morphability)

                                if 'requirements' in ability:
                                    for requirement in ability['requirements']:
                                        if 'building' in requirement:
                                            if ability['ability'] == morphability:
                                                return (unit['id'], morphability)
                                        if 'addon' in requirement:
                                            if ability['ability'] == morphability:
                                                return (unit['id'], morphability)

    def get_trainAbillity(self, name):
        for unit in self.unit:
            if unit['name'] == name:
                return self.bot._game_data.units[unit['id']].creation_ability.id.value
        for ability in self.ability:
            if ability['name'] == name:
                return ability['id']

    def get_trainBuilding(self, ability):
        for unit in self.unit:
            for abbility in unit['abilities']:
                if abbility['ability'] == self.get_trainAbillity(ability):
                    return UnitTypeId(unit['id'])

    def get_supplyBuilding(self):
        for unit in self.unit:
            if unit['supply'] == -8:
                if unit['race'] == self.bot.race_self:
                    return unit['name']
