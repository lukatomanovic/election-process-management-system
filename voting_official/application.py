from flask import Flask, request, Response, jsonify;
from configuration import Configuration;

# from models import database;
from flask_jwt_extended import JWTManager, get_jwt;

from roleCheckDecorator import roleCheck;
import csv;
import io;
from redis import Redis;
from datetime import datetime, timezone;
import pytz;

application = Flask(__name__);
application.config.from_object(Configuration);

jwt = JWTManager(application);


@application.route("/vote", methods=["POST"])
@roleCheck(role="zvanicnik")
def vote():
    try:
        file = request.files.get("file", None);
    except:
        return jsonify(message='Field file is missing.'), 400;

    if file is None:
        return jsonify(message='Field file is missing.'), 400;

    votingTimeStamp = datetime.now(timezone.utc).astimezone(pytz.timezone('Europe/Belgrade'));

    content = file.stream.read().decode ( "utf-8" );
    stream = io.StringIO(content);
    reader = csv.reader(stream);

    i = 0;
    for row in reader:
        if len(row) != 2:
            return jsonify(message="Incorrect number of values on line " + str(i) + "."), 400;
        try:
            number = int(row[1]);
            if number < 0:
                raise Exception();
        except:
            return jsonify(message="Incorrect poll number on line " + str(i) + "."), 400;
        i = i + 1;

    stream = io.StringIO(content);
    reader = csv.reader(stream);

    claims = get_jwt();
    jmbg = claims.get("jmbg","");

    for row in reader:
        with Redis(host=Configuration.REDIS_HOST) as redis:
            redis.rpush(Configuration.REDIS_VOTES_LIST, row[0]+"#"+row[1]+"#"+datetime.strftime(votingTimeStamp, "%Y-%m-%dT%H:%M:%S%z")+"#"+jmbg);

    return Response(status=200);


if (__name__ == "__main__"):
    # database.init_app(application);
    application.run(host="0.0.0.0", port=5002);
