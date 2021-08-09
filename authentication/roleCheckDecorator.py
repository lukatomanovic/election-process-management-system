from flask_jwt_extended import get_jwt, verify_jwt_in_request;
from functools import wraps
from flask import Response;


# u kojoj god aplikaciji da se koristi, potrebno je napraviti JWTManagera i inicijalizovati ga
def roleCheck(role):
    def innerRoleCheck(function):
        @wraps(function)
        def decorator(*arguments, **keywordArguments):
            verify_jwt_in_request();
            claims = get_jwt();
            if ("role" in claims) and (claims["role"] == role):
                return function(*arguments, **keywordArguments);
            else:
                return Response("Permission denied!", status=403);
        return decorator;
    return innerRoleCheck;
