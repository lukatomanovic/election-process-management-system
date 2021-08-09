from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime, ForeignKeyConstraint;
from sqlalchemy.ext.declarative import declarative_base;
from sqlalchemy.orm import relationship;

Base = declarative_base()

# ParticipationInElection = Table('participation_in_elections', Base.metadata,
#     Column('participantId', Integer, ForeignKey('participants.id'), primary_key=True),
#     Column('electionId', Integer, ForeignKey('elections.id'), primary_key=True),
#     Column('number', Integer, nullable=False)
# );


class ParticipationInElection(Base):
    __tablename__ = "participation_in_elections";

    participantId = Column(Integer, ForeignKey("participants.id"), primary_key=True, nullable=False);
    electionId = Column(Integer, ForeignKey("elections.id"), primary_key=True, nullable=False);

    # number representing ordinal number in election's list
    number = Column(Integer, nullable=False);
    result = Column(Integer, nullable=True);
    # votes = relationship('Vote', back_populates='participation_in_election');

class Participant(Base):
    __tablename__ = "participants";

    id = Column(Integer, primary_key=True);
    name = Column(String(256), nullable=False);
    individual = Column(Boolean, nullable=False);

    elections = relationship("Election", secondary=ParticipationInElection.__table__, back_populates="participants");

    def __repr__(self):
        return "{ id:"+str(self.id)+", name:"+self.name+", individual:"+str(self.individual)+"}";

    def to_json(self):
        return {
            'id': self.id,
            'name': self.name,
            'individual': self.individual
        }


class Election(Base):
    __tablename__ = "elections";

    id = Column(Integer, primary_key=True);
    startDate = Column(DateTime(timezone=True), nullable=False);
    endDate = Column(DateTime(timezone=True), nullable=False);
    start = Column(String(24), nullable=False);
    end = Column(String(24), nullable=False);
    individual = Column(Boolean, nullable=False);
    totalVotesNumber = Column(Integer, nullable=True);

    participants = relationship("Participant", secondary=ParticipationInElection.__table__, back_populates="elections");

    votes = relationship("Vote", back_populates="election");

    def to_json(self):
        return {
            'id': self.id,
            'start': self.start,
            'end': self.end,
            'individual': self.individual,
            'participants': [{"id": participant.id, "name": participant.name} for participant in self.participants]
        }


class Vote(Base):
    __tablename__ = "votes";

    id = Column(Integer, primary_key=True);
    guid = Column(String(36), nullable=False);
    electionId = Column(Integer, ForeignKey('elections.id'), nullable=False);
    poolNumber = Column(Integer, nullable=False);
    jmbg = Column(String(13), nullable=False);
    valid = Column(Boolean, nullable=False);
    reason_invalid = Column(String(256), nullable=True);

    election = relationship("Election", back_populates="votes");

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
    #
    # participation_in_election = relationship('ParticipationInElection', back_populates='votes');