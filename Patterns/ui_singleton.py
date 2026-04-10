"""
Only one SessionManager can ever exist. Stores the currently
logged-in user so any part of the app can access it without
passing the user object around everywhere.

"""
class SessionManager:

    _instance = None

    def __new__(cls):
        # if an instance already exists return it, never create a second one
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.current_user = None
        return cls._instance

    @property
    def user_id(self):
        if self.current_user:
            return self.current_user.get("id")
        return None

    def login(self, user: dict):
        self.current_user = user

    def logout(self):
        self.current_user = None

    def is_logged_in(self):
        return self.current_user is not None