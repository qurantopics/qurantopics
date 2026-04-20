

class UserAuthException(Exception):
	pass

class NoUserLoggedIn(UserAuthException):
	pass

class UserNotPermittedToPerformOperation(UserAuthException):
	pass
	