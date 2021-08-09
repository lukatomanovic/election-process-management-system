from flask import Flask, request, Response, jsonify;
from configuration import Configuration;

from models import database;
from models import Participant;
from models import Election;
from models import ParticipationInElection;
from models import Vote;

from flask_jwt_extended import JWTManager, jwt_required;

from sqlalchemy import and_, or_, cast;
from sqlalchemy import func;

from roleCheckDecorator import roleCheck;
import datetime;
import pytz;
import logging;

application = Flask(__name__);
application.config.from_object(Configuration);

jwt = JWTManager(application);


@application.route("/createParticipant", methods=["POST"])
@roleCheck(role="administrator")
def createParticipant():
    name = request.json.get("name", "");
    individual = request.json.get("individual", None);

    if len(name) == 0:
        return jsonify({'message': 'Field name is missing.'}), 400;
    if individual is None:
        return jsonify({'message': 'Field individual is missing.'}), 400;

    if len(name) > 256:
        return jsonify({'message': 'Field name is invalid.'}), 400;

    participant = Participant(name=name, individual=individual);

    database.session.add(participant);
    database.session.commit();

    return jsonify(id=participant.id), 200;


@application.route("/getParticipants", methods=["GET"])
@roleCheck(role="administrator")
def getParticipants():
    participants = Participant.query.all();
    return_participants_json_array=[];
    for participant in participants:
        return_participants_json_array.append({
            'id': participant.id,
            'name': participant.name,
            'individual': participant.individual
        });
    # return_participants_json_array=[ participant.to_json() for participant in participants];
    return jsonify(participants=return_participants_json_array), 200;


# {
# "start": ".....",
# "end": ".....",
# "individual": false,
# "participants": [1, .....],
# }
@application.route("/createElection", methods=["POST"])
@roleCheck(role="administrator")
def createElection():
    try:
        start = request.json.get("start", "");
        end = request.json.get("end", "");
        individual = request.json.get("individual", None);
        participants = request.json.get("participants", None);
    except:
        return jsonify(message='Field start is missing.'), 400;

    if len(start) == 0:
        return jsonify(message='Field start is missing.'), 400;
    if len(end) == 0:
        return jsonify(message='Field end is missing.'), 400;
    if individual is None or not isinstance(individual, bool):
        return jsonify(message='Field individual is missing.'), 400;
    if participants is None:
        return jsonify(message='Field participants is missing.'), 400;

    startDate = None;
    endDate = None;

    startPrepare = start;
    endPrepare = end;
    if len(start) == 19:
        startPrepare += "+0200";
    if len(end) == 19:
        endPrepare += "+0200";
    # noinspection PyBroadException
    try:
        # datetime.datetime.strptime('2019-01-04T16:41:24+0200', "%Y-%m-%dT%H:%M:%S%z");
        startDate = datetime.datetime.strptime(startPrepare, "%Y-%m-%dT%H:%M:%S%z");
        endDate = datetime.datetime.strptime(endPrepare, "%Y-%m-%dT%H:%M:%S%z");
        if endDate <= startDate:
            raise Exception()
    except:
        return jsonify(message='Invalid date and time.'), 400;

    # mysql dont change timezone, problem solved like this
    startDate = startDate.astimezone(pytz.timezone('Europe/Belgrade'));
    endDate = endDate.astimezone(pytz.timezone('Europe/Belgrade'));

    electionExists = Election.query.filter(and_(
        Election.startDate <= endDate, Election.endDate >= startDate
    )).count();

    if electionExists > 0:
        return jsonify(message='Invalid date and time.'), 400;

    if len(participants) < 2:
        return jsonify(message='Invalid participants.'), 400;

    for participant in participants:
        try:
            int(participant);
        except:
            return jsonify(message='Invalid participants.'), 400;

    participantsValid = Participant.query.filter(and_(
        or_(
            *[Participant.id == participant for participant in participants]
        ),
        Participant.individual == individual
    )).count();

    if len(participants) != participantsValid:
        return jsonify(message='Invalid participants.'), 400;

    election = Election(individual=individual, start=start, end=end, startDate=startDate, endDate=endDate,
                        totalVotesNumber=0);
    database.session.add(election);
    database.session.commit();

    message_time = str(datetime.datetime.now().replace(microsecond=0) + datetime.timedelta(hours=2)) + " # " + str(endDate) + " # "+str(startDate);
    logging.warning(msg=message_time)
    message_time = start + " # " + end;
    logging.warning(msg=message_time)
    number = 1;
    listOdParticipantNumbers = [];
    for participantId in participants:
        participantInElection = ParticipationInElection(participantId=participantId, electionId=election.id,
                                                        number=number, result=0);
        database.session.add(participantInElection);
        database.session.commit();
        listOdParticipantNumbers.append(number);
        number = number + 1;

    return jsonify(pollNumbers=listOdParticipantNumbers), 200;


@application.route("/getElections", methods=["GET"])
@roleCheck(role="administrator")
def getElections():
    elections = Election.query.all();
    return_elections_json_array = [];
    for election in elections:
        return_elections_json_array.append({
            'id': election.id,
            'start': election.start,
            'end': election.end,
            'individual': election.individual,
            'participants': [{"id": participant.id, "name": participant.name} for participant in election.participants]
        });
    return jsonify(elections=return_elections_json_array), 200;


@application.route("/getResults", methods=["GET"])
@roleCheck(role="administrator")
def getResults():
    try:
        electionId = request.args.get("id", None);
    except:
        return jsonify(message="Field id is missing."), 400;

    if electionId is None:
        return jsonify(message="Field id is missing."), 400;

    try:
        electionId = int(electionId);
    except:
        return jsonify(message="Election does not exist."), 400;

    election = Election.query.filter(Election.id == electionId).first();

    if election is None:
        return jsonify(message="Election does not exist."), 400;

    # current_time = datetime.datetime.now(datetime.timezone.utc).astimezone(pytz.timezone('Europe/Belgrade'));
    current_time = datetime.datetime.now().replace(microsecond=0) + datetime.timedelta(hours=2);
    election_time = election.endDate;
    # print(str(current_time));
    # print(str(election_time));
    message_time = str(election_time) + " # " + str(current_time);
    logging.warning(msg=message_time)
    if election_time > current_time:
        return jsonify(message="Election is ongoing."), 400;

    election_results = ParticipationInElection.query.join(Participant).filter(
        ParticipationInElection.electionId == election.id) \
        .with_entities(ParticipationInElection.participantId, Participant.name,
                       ParticipationInElection.number, ParticipationInElection.result).all();

    participant_results = [];
    for result in election_results:
        json_result_object = {
            "pollNumber": result.number,
            "name": result.name,
            "result": result.result,
            "percentage": 0,
            "final_result": 0
        }
        participant_results.append(json_result_object);
        
    if election.totalVotesNumber > 0 :
        if election.individual:
            calculate_result_presidential_elections(participant_results, election.totalVotesNumber);
        else:
            calculate_result_parliamentary_elections(participant_results, election.totalVotesNumber);

    return_results_array = [];
    for participant_result in participant_results:
        return_results_array.append({
            "pollNumber": participant_result["pollNumber"],
            "name": participant_result["name"],
            "result": participant_result["final_result"],
        })

    invalid_votes = Vote.query.filter(and_(
        Vote.electionId == election.id,
        Vote.valid == False
    )).all();

    return_invalid_votes_array = [];
    for vote in invalid_votes:
        return_invalid_votes_array.append({
            'electionOfficialJmbg': vote.jmbg,
            'ballotGuid': vote.guid,
            'pollNumber': vote.poolNumber,
            'reason': vote.reason_invalid
        });

    return jsonify(participants=return_results_array, invalidVotes=return_invalid_votes_array), 200;


def calculate_result_parliamentary_elections(participant_results, total_number_of_votes):
    mandate_number = 250;
    participants_in_calculation = [];
    for participant_result in participant_results:
        percentage = participant_result["result"] / total_number_of_votes;
        if percentage > 0.05:
            participants_in_calculation.append(participant_result)
        else:
            participant_result["final_result"] = 0;

    # sada radimo kalkulacije sa kandidatima koji su presli cenzus
    for participant_in_calculation in participants_in_calculation:
        participant_in_calculation["percentage"] = participant_in_calculation["result"];  # it is divided by 1

    while mandate_number > 0:
        max_position = -1;
        vote_number = -1
        i = 0;
        for participant_in_calculation in participants_in_calculation:
            if participant_in_calculation["percentage"] > vote_number:
                vote_number = participant_in_calculation["percentage"];
                max_position = i;
            i = i + 1;

        participants_in_calculation[max_position]["final_result"] += 1;
        participants_in_calculation[max_position]["percentage"] = \
            (participants_in_calculation[max_position]["result"] /
             (participants_in_calculation[max_position]["final_result"]+1));

        mandate_number -= 1;

    return


def calculate_result_presidential_elections(participant_results, total_number_of_votes):
    for participant_result in participant_results:
        participant_result["final_result"] = round(participant_result["result"] / total_number_of_votes, 2);
    return


@application.route("/", methods=["GET"])
def index():
    current_time = datetime.datetime.now(datetime.timezone.utc).astimezone(pytz.timezone('Europe/Belgrade'));
    return str(current_time);

if (__name__ == "__main__"):
    database.init_app(application);
    application.run(host="0.0.0.0", port=5001);
