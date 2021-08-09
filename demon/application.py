# from flask import Flask, request, Response, jsonify;
from configuration import Configuration;

from datetime import datetime,timezone;
from redis import Redis;
# import time;
# import pytz
from models import Election,ParticipationInElection, Participant, Vote;

from sqlalchemy import create_engine, and_, cast, DateTime;
from sqlalchemy.orm import sessionmaker
# from sqlalchemy import func, sql;

engine = create_engine(Configuration.SQLALCHEMY_DATABASE_URI, echo=False)
Session = sessionmaker(bind=engine)
session = Session()

# startDate = datetime.now(timezone.utc).astimezone(pytz.timezone('Europe/Belgrade'));
# print(startDate)
while True:
    try:
        print("pokusavam da se konektujem")
        with Redis(host=Configuration.REDIS_HOST) as redis:
            print("konektovao sam se")
            while True:
                bytesList = redis.lrange(Configuration.REDIS_VOTES_LIST, 0, 0);
                if len(bytesList) != 0:
                    bytes = redis.lpop(Configuration.REDIS_VOTES_LIST);
                    recieverVote = bytes.decode("utf-8");
                    voteData = recieverVote.split("#");
                    guid = voteData[0];
                    participantNumber = int(voteData[1]);
                    votingTime = datetime.strptime(voteData[2], "%Y-%m-%dT%H:%M:%S%z");
                    print(str(votingTime))
                    officialJMBG = voteData[3]
                    activeElection = session.query(Election).filter(and_(
                        Election.startDate <= votingTime,
                        Election.endDate >= votingTime
                    )).first();
                    print(str(votingTime))
                    if activeElection is None:
                        continue;

                    alreadyVoted = session.query(Vote).filter(Vote.guid == guid).count() != 0;

                    if alreadyVoted:
                        vote = Vote(guid=guid, electionId=activeElection.id, poolNumber=participantNumber,
                                    jmbg=officialJMBG, valid=False, reason_invalid="Duplicate ballot.");
                        session.add(vote);
                        session.commit();
                        continue;

                    participantExists = session.query(ParticipationInElection).filter(and_(
                        ParticipationInElection.electionId == activeElection.id,
                        ParticipationInElection.number == participantNumber
                    )).first();

                    if participantExists is None:
                        vote = Vote(guid=guid, electionId=activeElection.id, poolNumber=participantNumber,
                                    jmbg=officialJMBG, valid=False, reason_invalid="Invalid poll number.");
                        session.query(Election).filter(Election.id == activeElection.id) \
                            .update({'totalVotesNumber': Election.totalVotesNumber + 1});
                        session.add(vote);
                        session.commit();
                        continue;

                    session.query(ParticipationInElection).filter(and_(
                        ParticipationInElection.electionId == activeElection.id,
                        ParticipationInElection.participantId == participantExists.participantId
                    )).update({'result': participantExists.result + 1});

                    session.query(Election).filter(Election.id == activeElection.id)\
                        .update({'totalVotesNumber': Election.totalVotesNumber + 1});

                    vote = Vote(guid=guid, electionId=activeElection.id, poolNumber=participantNumber,
                                jmbg=officialJMBG, valid=True);
                    session.add(vote);
                    session.commit();
    except Exception as error:
        print(error);

            # print(str(session.query(Election).all()));
    # time.sleep(5);
    # participant = Participant (name="PA2",individual=True);
    # session.add(participant);
    # session.commit()
    # election=Election(startDate=datetime.strptime("2021-06-16T15:55:46+0100", "%Y-%m-%dT%H:%M:%S%z"), endDate=datetime.strptime("2021-07-12T15:55:46+0100", "%Y-%m-%dT%H:%M:%S%z"),start="2021-06-16T15:55:46+0100", end="2021-07-12T15:55:46+0100", individual=True);
    # session.add(election);
    # session.commit();
    # partele=ParticipationInElection(participantId=participant.id, electionId=election.id, number=1);
    # session.add(partele);
    # session.commit()
    # # print(str(session.query(Participant).all()));
    # # print(str(session.query(Election).all()));
    # # print(str(session.query(ParticipationInElection).all()));
    #
    # # da li postoje aktivni izbori
    # # 2021-07-12T15:55:46
    # result = session.query(Election).filter(and_(
    #     Election.startDate <= datetime.strptime("2021-07-12 02:16:58+02:00", "%Y-%m-%dT%H:%M:%S%z"),
    #     # Election.endDate >= datetime.strptime("2021-07-12T12:55:46-0800", "%Y-%m-%dT%H:%M:%S%z")
    #     Election.endDate >= datetime.strptime("2021-07-12T12:55:46-0800", "%Y-%m-%dT%H:%M:%S%z")
    # )).all()
    #
    # print(str(result));
# d1=datetime.strptime("2021-07-12T02:16:58+0200", "%Y-%m-%dT%H:%M:%S%z");
# result = session.query(Election).filter(and_(
#     Election.startDate <= d1,
#     Election.endDate >= d1
# )).all()
# session.close();





