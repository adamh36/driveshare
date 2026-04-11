"""
MEDIATOR PATTERN: UI Coordinator
CIS 476 Term Project: DriveShare

DriveShareMediator coordinates all communication between UI components.
Components never talk to each other directly — they send events here
and the mediator decides what happens.

Pattern roles:
  Mediator           -> Mediator (abstract)
  ConcreteMediator   -> DriveShareMediator
  Colleague          -> UIComponent (abstract)
  ConcreteColleagues -> NavPanel, StatusBar, ContentPanel, all Frame classes
"""

# CONCRETE COLLEAGUES (defined in their respective files)
# app.py          -> NavPanel, StatusBar, ContentPanel
# gui/auth_frames.py    -> LoginFrame, RegisterFrame, ForgotPasswordFrame
# gui/main_frames.py    -> DashboardFrame, SearchFrame, ListCarFrame,
#                          MyListingsFrame, MyBookingsFrame
# gui/secondary_frames.py -> MessagesFrame, NotificationsFrame, ReviewsFrame
#
# All of the above inherit from UIComponent and are registered
# with DriveShareMediator in app.py via mediator.register()

from abc import ABC, abstractmethod


# MEDIATOR INTERFACE (abstract)
# defines the contract every mediator must follow
# any class that wants to coordinate UI components MUST implement
# register() to add components and handle() to route events between them
class Mediator(ABC):

    @abstractmethod
    def register(self, name: str, component: 'UIComponent') -> None: pass

    @abstractmethod
    def handle(self, sender: 'UIComponent', event: str, data=None) -> None: pass


# COLLEAGUE INTERFACE (abstract)
# base class for every UI component in the app
# holds a reference to the mediator and uses it to communicate
# components never talk to each other directly — they always go through notify()
class UIComponent(ABC):

    def __init__(self, mediator: Mediator) -> None:
        self._mediator = mediator

    def notify(self, event: str, data=None) -> None:
        self._mediator.handle(self, event, data)


# CONCRETE MEDIATOR
# central coordinator — routes events between registered components
# knows all registered colleagues and decides what to do for each event
class DriveShareMediator(Mediator):

    def __init__(self) -> None:
        self._components = {}

    def register(self, name: str, component: UIComponent) -> None:
        self._components[name] = component

    def handle(self, sender: UIComponent, event: str, data=None) -> None:

        if event == "navigate":
            content = self._components.get("content")
            if content:
                content.show_frame(data)

        elif event == "login_success":
            nav    = self._components.get("nav")
            status = self._components.get("status_bar")
            if nav:
                nav.show_logged_in()
            if status and data:
                status.set_user(data)
            content = self._components.get("content")
            if content:
                content.show_frame("dashboard")

        elif event == "logout":
            nav    = self._components.get("nav")
            status = self._components.get("status_bar")
            if nav:
                nav.show_logged_out()
            if status:
                status.clear_user()
            content = self._components.get("content")
            if content:
                content.show_frame("login")

        elif event in ("booking_created", "car_listed", "notification_update"):
            content = self._components.get("content")
            if content:
                content.refresh_current()