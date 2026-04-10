"""
MEDIATOR PATTERN: UI Coordinator
CIS 476 Term Project: DriveShare

DriveShareMediator coordinates all communication between UI components.
Components never talk to each other directly — they send events here
and the mediator decides what happens.

Pattern roles:
  Mediator           -> DriveShareMediator
  Abstract Colleague -> UIComponent
  Concrete Colleagues -> NavPanel, StatusBar, ContentPanel, all Frame classes
"""


class UIComponent:
    """
    Base class for every UI component in the app.
    Call self.notify(event, data) to communicate through the mediator.
    """

    def __init__(self, mediator):
        self._mediator = mediator

    def notify(self, event, data=None):
        self._mediator.handle(self, event, data)


class DriveShareMediator:
    """
    Central coordinator. Routes events between registered components.
    """

    def __init__(self):
        self._components = {}

    def register(self, name, component):
        self._components[name] = component

    def handle(self, sender, event, data=None):

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