"""
BUILDER PATTERN - Car Listing
CIS 476 Term Project: DriveShare

Purpose:
Separate the construction of a complex CarListing object from its representation.
The Builder pattern fits perfectly here because a car listing has required fields
(make, model, year, price, location) and optional ones (description, mileage, availability)
that owners may or may not fill in.

Roles:
Product: CarListing
Builder: CarListingBuilder
ConcreteBuilder: FullCarListingBuilder
Director: ListingDirector
"""

from abc import ABC, abstractmethod
from database import get_connection


# PRODUCT
# this represents one car listing row in the database
class CarListing:

    def __init__(self):
        # required: these must be set for the listing to be valid
        self.ownerId = None
        self.make = None
        self.model = None
        self.year = None
        self.mileage = None
        self.location = None
        self.pricePerDay = None

        # optional: owner can leave these blank
        self.description = None
        self.available = 1  # default to available when first listed

    # setters for required fields
    def setOwnerId(self, ownerId): self.ownerId = ownerId
    def setMake(self, make): self.make = make
    def setModel(self, model): self.model = model
    def setYear(self, year): self.year = year
    def setMileage(self, mileage): self.mileage = mileage
    def setLocation(self, location): self.location = location
    def setPricePerDay(self, price): self.pricePerDay = price

    # setters for optional fields
    def setDescription(self, description): self.description = description
    def setAvailable(self, available): self.available = available

    def saveToDB(self):
        # once the listing is fully built, this pushes it into the cars table
        conn = get_connection()
        cursor = conn.cursor()

        # The saveToDB() method inserts the fully built car listing into the cars table in the database.
        # Each ? is a placeholder that gets replaced in order by the actual values from the listing object,
        # which I believe to be safer than putting the values directly into the query.
        cursor.execute("""
            INSERT INTO cars (owner_id, make, model, year, mileage, location, price_per_day, description, available)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?) """, (
            self.ownerId,
            self.make,
            self.model,
            self.year,
            self.mileage,
            self.location,
            self.pricePerDay,
            self.description,
            self.available
        ))
        conn.commit()
        conn.close()

    def display(self):
        print("Car Listing:")
        print(f"Owner ID  : {self.ownerId}")
        print(f"Car       : {self.year} {self.make} {self.model}")
        print(f"Price     : ${self.pricePerDay} / day")
        print(f"Location  : {self.location}")
        print(f"Mileage   : {self.mileage} miles")
        print(f"Available : {'Yes' if self.available else 'No'}")
        print(f"Notes     : {self.description}")


# ABSTRACT BUILDER
# defines the steps every builder must implement
class CarListingBuilder(ABC):

    # required steps
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

    # optional steps
    @abstractmethod
    def buildDescription(self): pass

    @abstractmethod
    def getResult(self): pass


# CONCRETE BUILDER
# takes in all the form data and knows how to plug it into the CarListing
class FullCarListingBuilder(CarListingBuilder):

    def __init__(self, ownerId, make, model, year,
                 mileage, location, pricePerDay, description=None):

        # saving all the input so each build method can grab what it needs
        self.ownerId = ownerId
        self.make = make
        self.model = model
        self.year = year
        self.mileage = mileage
        self.location = location
        self.pricePerDay = pricePerDay
        self.description = description  # optional, can be None

        # start with a blank listing, director will fill it in step by step
        self.listing = CarListing()

    def buildOwnerInfo(self):
        # ties the listing to whoever is logged in
        self.listing.setOwnerId(self.ownerId)

    def buildCarDetails(self):
        # the core car identity
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
        # only set if the owner actually wrote something
        if self.description:
            self.listing.setDescription(self.description)

    def getResult(self):
        # hand back the fully assembled listing
        return self.listing


# DIRECTOR
# controls what gets built and in what order
# doesn't know HOW things are built, just which steps to call
class ListingDirector:

    def constructFullListing(self, builder):
        # all steps: use this when the owner fills in everything
        builder.buildOwnerInfo()
        builder.buildCarDetails()
        builder.buildPricing()
        builder.buildLocation()
        builder.buildMileage()
        builder.buildDescription()

    def constructMinimalListing(self, builder):
        # required steps only: use this if description is skipped
        builder.buildOwnerInfo()
        builder.buildCarDetails()
        builder.buildPricing()
        builder.buildLocation()
        builder.buildMileage()


# this is how it'll be called from the owner dashboard in the real app
# the session gives us the ownerID, the form gives us everything else
#
# builder = FullCarListingBuilder(
#     ownerId     = session["user_id"],
#     make        = st.session_state["make"],
#     model       = st.session_state["model"],
#     year        = st.session_state["year"],
#     mileage     = st.session_state["mileage"],
#     location    = st.session_state["location"],
#     pricePerDay = st.session_state["price_per_day"],
#     description = st.session_state.get("description")
# )
#
# director = ListingDirector()
# director.constructFullListing(builder)
# builder.getResult().saveToDB()


# MAIN: just for testing and debugging the pattern works before wiring up the UI
if __name__ == "__main__":

    director = ListingDirector()

    # full listing with a description
    builder = FullCarListingBuilder(
        ownerId=1,
        make="Toyota",
        model="Camry",
        year=2022,
        mileage=32000,
        location="Dearborn, MI",
        pricePerDay=55.00,
        description="Clean car, non-smoker..."
    )

    director.constructFullListing(builder)

    print("\n[Full Listing]")
    builder.getResult().display()

    # minimal listing, no description
    minBuilder = FullCarListingBuilder(
        ownerId=2,
        make="Honda",
        model="Civic",
        year=2021,
        mileage=18000,
        location="Detroit, MI",
        pricePerDay=45.00
    )

    director.constructMinimalListing(minBuilder)

    print("\n[Minimal Listing]")
    minBuilder.getResult().display()