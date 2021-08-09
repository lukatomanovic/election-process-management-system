from flask_sqlalchemy import SQLAlchemy;
from sqlalchemy import ForeignKeyConstraint;

database = SQLAlchemy();


class ParticipationInElection(database.Model):
    __tablename__ = "participation_in_elections";

    participantId = database.Column(database.Integer, database.ForeignKey("participants.id"), primary_key=True, nullable=False);
    electionId = database.Column(database.Integer, database.ForeignKey("elections.id"), primary_key=True, nullable=False);

    # number representing ordinal number in election's list
    number = database.Column(database.Integer, nullable=False);
    result = database.Column(database.Integer, nullable=True);
    # votes = database.relationship('Vote', back_populates='participation_in_election');


class Participant(database.Model):
    __tablename__ = "participants";

    id = database.Column(database.Integer, primary_key=True);
    name = database.Column(database.String(256), nullable=False);
    individual = database.Column(database.Boolean, nullable=False);

    elections = database.relationship("Election", secondary=ParticipationInElection.__table__, back_populates="participants");

    def __repr__(self):
        return "{ id:"+str(self.id)+", name:"+self.name+", individual:"+str(self.individual)+"}";

    def to_json(self):
        return {
            'id': self.id,
            'name': self.name,
            'individual': self.individual,
        }


class Election(database.Model):
    __tablename__ = "elections";

    id = database.Column(database.Integer, primary_key=True);
    startDate = database.Column(database.DateTime(timezone=True), nullable=False);
    endDate = database.Column(database.DateTime(timezone=True), nullable=False);
    start = database.Column(database.String(24), nullable=False);
    end = database.Column(database.String(24), nullable=False);
    individual = database.Column(database.Boolean, nullable=False);
    totalVotesNumber = database.Column(database.Integer, nullable=True);

    participants = database.relationship("Participant", secondary=ParticipationInElection.__table__, back_populates="elections");

    votes = database.relationship("Vote", back_populates="election");

    def to_json(self):
        return {
            'id': self.id,
            'start': self.start,
            'end': self.end,
            'individual': self.individual,
            'participants': [{"id": participant.id, "name": participant.name} for participant in self.participants]
        }


class Vote(database.Model):
    __tablename__ = "votes";

    id = database.Column(database.Integer, primary_key=True);
    guid = database.Column(database.String(36), nullable=False);
    electionId = database.Column(database.Integer, database.ForeignKey('elections.id'), nullable=False);
    poolNumber = database.Column(database.Integer, nullable=False);
    jmbg = database.Column(database.String(13), nullable=False);
    valid = database.Column(database.Boolean, nullable=False);
    reason_invalid = database.Column(database.String(256), nullable=True);

    election = database.relationship("Election", back_populates="votes");

    def to_json(self):
        return {
            'electionOfficialJmbg': self.jmbg,
            'ballotGuid': self.guid,
            'pollNumber': self.poolNumber,
            'reason': self.reason_invalid
        }

    # __table_args__ = (
    #     ForeignKeyConstraint(
    #         ['electionId', 'participantId'],
    #         ['participation_in_elections.electionId', 'participation_in_elections.participantId'],
    #     ),
    # )

    # participation_in_election = database.relationship('ParticipationInElection', back_populates='votes');
