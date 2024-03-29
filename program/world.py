#! /usr/bin/env python

import matplotlib.pyplot as plt
import argparse
from collections import defaultdict
import json
import math

import matplotlib as mil
mil.use('TkAgg')


class Agent:

    """
    >>> agent = Agent(30, age=84, agreeableness=42)
    >>> agent.position
    30
    >>> agent.age
    84
    >>> agent.agreeableness
    42
    """

    def __init__(self, position, **properties):
        self.position = position
        for property_name, property_value in properties.items():
            setattr(self, property_name, property_value)


class Position:

    def __init__(self, longitude_degrees, latitude_degrees):

        assert -180 <= longitude_degrees <= 180
        self.longitude_degrees = longitude_degrees

        assert -90 <= latitude_degrees <= 90
        self.latitude_degrees = latitude_degrees

    @property
    def longitude(self):
        """Longitude in radians"""
        return self.longitude_degrees * math.pi / 180

    @property
    def latitude(self):
        """Latitude in radians"""
        return self.latitude_degrees * math.pi / 180


class Zone:
    """
    A rectangular geographic area bounded by two corners. The corners can
    be top-left and bottom right, or top-right and bottom-left so you should be
    careful when computing the distances between them.
    """

    ZONES = []
    # The width and height of the zones that will be added to ZONES. Here, we
    # choose square zones but we could just as well use rectangular shapes.

    MIN_LONGITUDE_DEGREES = -180
    MAX_LONGITUDE_DEGREES = 180
    MIN_LATITUDE_DEGREES = -90
    MAX_LATITUDE_DEGREES = 90
    WIDTH_DEGREES = 1
    HEIGHT_DEGREES = 1

    EARTH_RADIUS_KILOMETERS = 6371

    def __init__(self, corner1, corner2):
        self.corner1 = corner1
        self.corner2 = corner2
        self.inhabitants = []

    @property
    def population(self):
        """Number of inhabitants in the zone"""
        return len(self.inhabitants)

    @property
    def width(self):
        """Zone width, in kilometers"""
        return abs(self.corner1.longitude - self.corner2.longitude) * self.EARTH_RADIUS_KILOMETERS

    @property
    def height(self):
        """Zone height, in kilometers"""
        return abs(self.corner1.latitude - self.corner2.latitude) * self.EARTH_RADIUS_KILOMETERS

    def add_inhabitant(self, inhabitant):
        self.inhabitants.append(inhabitant)

    def population_density(self):
        """Population density of the zone, (people/km²)"""
        return self.population / self.area()

    def area(self):
        """Compute the zone area, in square kilometers"""
        return self.height * self.width

    def average_agreeableness(self):
        if not self.inhabitants:
            return 0
        return sum([inhabitant.agreeableness for inhabitant in self.inhabitants]) / self.population

    def contains(self, position):
        """Return True if the zone contains this position"""
        return position.longitude >= min(self.corner1.longitude, self.corner2.longitude) and \
            position.longitude < max(self.corner1.longitude, self.corner2.longitude) and \
            position.latitude >= min(self.corner1.latitude, self.corner2.latitude) and \
            position.latitude < max(
                self.corner1.latitude, self.corner2.latitude)

    @classmethod
    def find_zone_that_contains(cls, position):
        if not cls.ZONES:
            # Initialize zones automatically if necessary
            cls._initialize_zones()

        # Compute the index in the ZONES array that contains the given position
        longitude_index = int(
            (position.longitude_degrees - cls.MIN_LONGITUDE_DEGREES) / cls.WIDTH_DEGREES)
        latitude_index = int(
            (position.latitude_degrees - cls.MIN_LATITUDE_DEGREES) / cls.HEIGHT_DEGREES)
        longitude_bins = int((cls.MAX_LONGITUDE_DEGREES -
                              cls.MIN_LONGITUDE_DEGREES) / cls.WIDTH_DEGREES)  # 180-(-180) / 1
        zone_index = latitude_index * longitude_bins + longitude_index

        # Just checking that the index is correct
        zone = cls.ZONES[zone_index]
        assert zone.contains(position)

        return zone

    @classmethod
    def _initialize_zones(cls):
        cls.ZONES = []
        for latitude in range(cls.MIN_LATITUDE_DEGREES, cls.MAX_LATITUDE_DEGREES, cls.HEIGHT_DEGREES):
            for longitude in range(cls.MIN_LONGITUDE_DEGREES, cls.MAX_LONGITUDE_DEGREES, cls.WIDTH_DEGREES):
                bottom_left_corner = Position(longitude, latitude)
                top_right_corner = Position(
                    longitude + cls.WIDTH_DEGREES, latitude + cls.HEIGHT_DEGREES)
                zone = Zone(bottom_left_corner, top_right_corner)
                cls.ZONES.append(zone)


class BaseGraph:

    def __init__(self):
        self.show_grid = True

        self.title = "Your graph title"
        self.x_label = "X-axis label"
        self.y_label = "X-axis label"

    def show(self, zones):
        x_values, y_values = self.xy_values(zones)
        self.plot(x_values, y_values)

        plt.xlabel(self.x_label)
        plt.ylabel(self.y_label)
        plt.title(self.title)
        plt.grid(self.show_grid)
        plt.show()

    def plot(self, x_values, y_values):
        """Override this method to create different kinds of graphs, such as histograms"""
        # http://matplotlib.org/api/pyplot_api.html#matplotlib.pyplot.plot
        plt.plot(x_values, y_values, '.')

    def xy_values(self, zones):
        """
        Returns:
            x_values
            y_values
        """
        # You should implement this method in your children classes
        raise NotImplementedError

    def _stat_by_age(self, zones, property_name):
        stat_by_age = defaultdict(float)
        population_by_age = defaultdict(int)

        for zone in zones:
            for inhabitant in zone.inhabitants:
                stat_by_age[inhabitant.age] += getattr(
                    inhabitant, property_name)
                population_by_age[inhabitant.age] += 1

        x_values = range(0, 100)
        y_values = [stat_by_age[age] /
                    (population_by_age[age] or 1) for age in range(0, 100)]
        return x_values, y_values


class AgreeablenessGraph(BaseGraph):

    def __init__(self):
        super(AgreeablenessGraph, self).__init__()

        self.title = "Nice people live in the countryside"
        self.x_label = "population density"
        self.y_label = "agreeableness"

    def xy_values(self, zones):
        x_values = [zone.population_density() for zone in zones]
        y_values = [zone.average_agreeableness() for zone in zones]
        return x_values, y_values


class IncomeGraph(BaseGraph):

    def __init__(self):
        super(IncomeGraph, self).__init__()

        self.title = "Older people have more money"
        self.x_label = "age"
        self.y_label = "income"

    def xy_values(self, zones):
        return self._stat_by_age(zones, "income")


class AgreeablenessPerAgeGraph(BaseGraph):

    def __init__(self):
        super(AgreeablenessPerAgeGraph, self).__init__()
        self.title = "Nice people are young"
        self.x_label = "age"
        self.y_label = "agreeableness"

    def xy_values(self, zones):
        return self._stat_by_age(zones, "agreeableness")


def main():
    parser = argparse.ArgumentParser("Display population stats")
    parser.add_argument("src", help="Path to source json agents file")
    args = parser.parse_args()

    for agent_properties in json.load(open(args.src)):
        longitude = agent_properties.pop('longitude')
        latitude = agent_properties.pop('latitude')
        position = Position(longitude, latitude)
        zone = Zone.find_zone_that_contains(position)
        agent = Agent(position, **agent_properties)
        zone.add_inhabitant(agent)

    agreeableness_graph = AgreeablenessGraph()
    agreeableness_graph.show(Zone.ZONES)

    agreeableness_per_age_graph = AgreeablenessPerAgeGraph()
    agreeableness_per_age_graph.show(Zone.ZONES)

    income_graph = IncomeGraph()
    income_graph.show(Zone.ZONES)


if __name__ == "__main__":
    main()
