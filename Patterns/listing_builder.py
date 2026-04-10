"""
BUILDER PATTERN - Car Listing
CIS 476 Term Project: DriveShare

Separates the construction of a CarListing object from its representation.
Required fields: make, model, year, price, location.
Optional fields: description, mileage, availability.

Roles:
  Product:         CarListing
  Builder:         CarListingBuilder (abstract)
  ConcreteBuilder: FullCarListingBuilder
  Director:        ListingDirector
"""

from abc import ABC, abstractmethod
from db.database import get_connection


class CarListing:
    # the product — represents one car listing row in the database

    def __init__(self):
        self.ownerId     = None
        self.make        = None
        self.model       = None
        self.year        = None
        self.mileage     = None
        self.location    = None
        self.pricePerDay = None
        self.description = None
        self.available   = 1  # default to available when first listed

    def setOwnerId(self, ownerId):       self.ownerId     = ownerId
    def setMake(self, make):             self.make        = make
    def setModel(self, model):           self.model       = model
    def setYear(self, year):             self.year        = year
    def setMileage(self, mileage):       self.mileage     = mileage
    def setLocation(self, location):     self.location    = location
    def setPricePerDay(self, price):     self.pricePerDay = price
    def setDescription(self, desc):      self.description = desc
    def setAvailable(self, available):   self.available   = available

    def saveToDB(self):
        # insert the fully built listing into the cars table
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO cars (owner_id, make, model, year, mileage, location,
                              price_per_day, description, available)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            self.ownerId, self.make, self.model, self.year,
            self.mileage, self.location, self.pricePerDay,
            self.description, self.available
        ))
        conn.commit()
        conn.close()


class CarListingBuilder(ABC):
    # abstract builder — defines the steps every builder must implement

    @abstractmethod
    def buildOwnerInfo(self): pass

    @abstractmethod
    def buildCarDetails(self): pass

    @abstractmethod
    def buildPricing(self): pass

    @abstractmethod
    def buildLocation(self): pass

    @abstractmethod
    def buildMileage(self): pass

    @abstractmethod
    def buildDescription(self): pass

    @abstractmethod
    def getResult(self): pass


class FullCarListingBuilder(CarListingBuilder):
    # concrete builder — takes all form data and plugs it into CarListing step by step

    def __init__(self, ownerId, make, model, year,
                 mileage, location, pricePerDay, description=None):
        self.ownerId     = ownerId
        self.make        = make
        self.model       = model
        self.year        = year
        self.mileage     = mileage
        self.location    = location
        self.pricePerDay = pricePerDay
        self.description = description
        self.listing     = CarListing()

    def buildOwnerInfo(self):
        self.listing.setOwnerId(self.ownerId)

    def buildCarDetails(self):
        self.listing.setMake(self.make)
        self.listing.setModel(self.model)
        self.listing.setYear(self.year)

    def buildPricing(self):
        self.listing.setPricePerDay(self.pricePerDay)

    def buildLocation(self):
        self.listing.setLocation(self.location)

    def buildMileage(self):
        self.listing.setMileage(self.mileage)

    def buildDescription(self):
        if self.description:
            self.listing.setDescription(self.description)

    def getResult(self):
        return self.listing


class ListingDirector:
    # director — controls which steps get called and in what order

    def constructFullListing(self, builder):
        # all steps including optional description
        builder.buildOwnerInfo()
        builder.buildCarDetails()
        builder.buildPricing()
        builder.buildLocation()
        builder.buildMileage()
        builder.buildDescription()

    def constructMinimalListing(self, builder):
        # required steps only, skips description
        builder.buildOwnerInfo()
        builder.buildCarDetails()
        builder.buildPricing()
        builder.buildLocation()
        builder.buildMileage()