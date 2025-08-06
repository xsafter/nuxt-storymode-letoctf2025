from CTFd.models import db, Challenges, Teams, Users
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime

class StorylineChallenge(db.Model):
    __tablename__ = 'storyline_challenges'

    id = Column(Integer, ForeignKey('challenges.id'), primary_key=True)
    predecessor_id = Column(Integer, ForeignKey('challenges.id'), nullable=True)
    max_lifetime = Column(Integer, nullable=True)

    challenge = relationship("Challenges", foreign_keys=[id], backref="storyline_data")
    predecessor = relationship("Challenges", foreign_keys=[predecessor_id])

class SolutionDescription(db.Model):
    __tablename__ = 'solution_descriptions'

    id = Column(Integer, primary_key=True)
    team_id = Column(Integer, ForeignKey('teams.id'), nullable=False)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    challenge_id = Column(Integer, ForeignKey('challenges.id'), nullable=False)
    description = Column(Text, nullable=False)
    submitted_at = Column(DateTime, default=datetime.utcnow)

    team = relationship("Teams", backref="solution_descriptions")
    user = relationship("Users", backref="solution_descriptions")
    challenge = relationship("Challenges", backref="solution_descriptions")
