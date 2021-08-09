from flask import Flask, request, Response, jsonify;
from configuration import Configuration;
from models import database;
from email.utils import parseaddr;
from re import match, search;
from models import User, Role;
from flask_jwt_extended import JWTManager, create_access_token, create_refresh_token, jwt_required, get_jwt, \
    get_jwt_identity;
from sqlalchemy import and_;
from roleCheckDecorator import roleCheck;

application = Flask(__name__);
application.config.from_object(Configuration);
jwt = JWTManager(application);  # init with secret key given in app config

def is_jmbg_valid(jmbg):
    result = match('^[0-9]{13}$', jmbg);
    if result is None:
        return False;

    day = int(jmbg[0:2]);
    month = int(jmbg[2:4]);
    year = int(jmbg[4:7]);

    isLeapYear = False;
    if (year % 4) == 0:
        if ((year % 100) == 0) and ((year % 400) == 0):
            isLeapYear = True;
        else:
            isLeapYear = True;

    if (month in [1, 3, 5, 7, 8, 10, 12]) and day > 31:
        return False;
    elif (month in [4, 6, 9, 11]) and day > 30:
        return False;
    elif (month == 2 and isLeapYear and day > 29) or (month == 2 and not isLeapYear and day > 28):
        return False;

    region = int(jmbg[7:9]);
    if region < 70 or region > 99:
        return False;

    # genderId 0-999 - no check
    genderId = int(jmbg[9:12]);

    # DDMMYYYRRBBBK = ab cd efg hij klm
    # m = 11 − (( 7*(a+g) + 6*(b+h) + 5*(c+i) + 4*(d+j) + 3*(e+k) + 2*(f+l) ) mod 11)
    controlNum = int(jmbg[12:13]);
    m = 11 - (7 * (int(jmbg[0]) + int(jmbg[6])) + 6 * (int(jmbg[1]) + int(jmbg[7])) + 5 * (int(jmbg[2]) + int(jmbg[8]))
              + 4 * (int(jmbg[3]) + int(jmbg[9])) + 3 * (int(jmbg[4]) + int(jmbg[10])) + 2 * (
                      int(jmbg[5]) + int(jmbg[11]))) % 11;
    k = m;
    if m > 9:
        k = 0;
    if k != controlNum:
        return False;
    return True;


def is_email_valid(email):
    if len(email) > 256:
        return False;
    result = match('[^@]+@.*\.[a-z]{2,}$', email);
    if result is None:
        return False;
    return True;


def is_password_valid(password):
    if len(password) < 8 or len(password) > 256:
        return False;
    elif search('[0-9]', password) is None:
        return False;
    elif search('[A-Z]', password) is None:
        return False;
    elif search('[a-z]', password) is None:
        return False;
    return True;


# {
# "jmbg": ".....",
# "forename": ".....",
# "surname": ".....",
# "email": ".....",
# "password": "....."
# }

@application.route("/register", methods=["POST"])
def register():
    try:
        jmbg = request.json.get("jmbg", "");
        forename = request.json.get("forename", "");
        surname = request.json.get("surname", "");
        email = request.json.get("email", "");
        password = request.json.get("password", "");
    except:
        return jsonify({'message': 'Field jmbg is missing.'}), 400;

    isJMBGEmpty = len(jmbg) == 0;
    isForenameEmpty = len(forename) == 0;
    isSurnameEmpty = len(surname) == 0;
    isEmailEmpty = len(email) == 0;
    isPasswordEmpty = len(password) == 0;

    # check required fields
    if isJMBGEmpty:
        return jsonify({'message': 'Field jmbg is missing.'}), 400;
    if isForenameEmpty:
        return jsonify({'message': 'Field forename is missing.'}), 400;
    if isSurnameEmpty:
        return jsonify({'message': 'Field surname is missing.'}), 400;
    if isEmailEmpty:
        return jsonify({'message': 'Field email is missing.'}), 400;
    if isPasswordEmpty:
        return jsonify({'message': 'Field password is missing.'}), 400;

    # check jmbg format
    if not is_jmbg_valid(jmbg):
        return jsonify({'message': 'Invalid jmbg.'}), 400;

    # check email format
    # emailResultCheck = parseaddr(email);
    if not is_email_valid(email):
        return jsonify({'message': 'Invalid email.'}), 400;
    # check password format
    if not is_password_valid(password):
        return jsonify({'message': 'Invalid password.'}), 400;

    emailExistsCheck = User.query.filter(User.email == email).first();
    if emailExistsCheck is not None:
        return jsonify({'message': 'Email already exists.'}), 400;

    role = Role.query.filter(Role.name == "zvanicnik").first();

    try:
        user = User(jmbg=jmbg, forename=forename, surname=surname, email=email, password=password, roleId=role.id);
        database.session.add(user);
        database.session.commit();
    except:
        return jsonify({'message': 'Jmbg already exists.'}), 400;

    return Response(status=200);


# {
# "email": ".....",
# "password": "....."
# }
@application.route("/login", methods=["POST"])
def login():
    try:
        email = request.json.get("email", "");
        password = request.json.get("password", "");
    except:
        return jsonify({'message': 'Field email is missing.'}), 400;

    isEmailEmpty = len(email) == 0;
    isPasswordEmpty = len(password) == 0;
    if isEmailEmpty:
        return jsonify({'message': 'Field email is missing.'}), 400;
    if isPasswordEmpty:
        return jsonify({'message': 'Field password is missing.'}), 400;
    # emailResultCheck = parseaddr(email);
    if not is_email_valid(email):
        return jsonify({'message': 'Invalid email.'}), 400;

    user = User.query.filter(and_(User.email == email, User.password == password)).first();

    if user is None:
        return jsonify({'message': 'Invalid credentials.'}), 400;

    additionalClaims = {
        "jmbg": user.jmbg,
        "forename": user.forename,
        "surname": user.surname,
        "role": str(user.role)
    }

    accessToken = create_access_token(identity=user.email, additional_claims=additionalClaims);
    refreshToken = create_refresh_token(identity=user.email, additional_claims=additionalClaims);

    return jsonify(accessToken=accessToken, refreshToken=refreshToken), 200;


# refresh = True -> znaci da parametar mora biti JSON Web Token refresh tipa
@application.route("/refresh", methods=["POST"])
@jwt_required(refresh=True)
def refresh():
    identity = get_jwt_identity();
    refreshClaims = get_jwt();

    additionalClaims = {
        "jmbg": refreshClaims["jmbg"],
        "forename": refreshClaims["forename"],
        "surname": refreshClaims["surname"],
        "role": refreshClaims["role"]
    }

    accessToken = create_access_token(identity=identity, additional_claims=additionalClaims);

    return jsonify(accessToken=accessToken), 200;


# refresh = True -> znaci da parametar mora biti JSON Web Token refresh tipa

@application.route("/delete", methods=["POST"])
@roleCheck(role="administrator")
def delete():
    try:
        email = request.json.get("email", "");
    except:
        return jsonify({'message': 'Field email is missing.'}), 400;

    isEmailEmpty = len(email) == 0;
    if isEmailEmpty:
        return jsonify({'message': 'Field email is missing.'}), 400;
    # emailResultCheck = parseaddr(email);
    if not is_email_valid(email):
        return jsonify({'message': 'Invalid email.'}), 400;

    user = User.query.filter(User.email == email).one_or_none();
    if user is None:
        return jsonify({'message': 'Unknown user.'}), 400;

    database.session.delete(user);
    database.session.commit();
    return Response(status=200);


@application.route("/check", methods=["POST"])
@jwt_required()
def check():
    return "Token is valid.";


@application.route("/", methods=["GET"])
def index():
    return "Hello world";

if (__name__ == "__main__"):
    database.init_app(application);
    application.run(host="0.0.0.0", port=5003);
