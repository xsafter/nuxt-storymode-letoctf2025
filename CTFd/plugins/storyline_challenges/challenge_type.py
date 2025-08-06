from CTFd.plugins.challenges import BaseChallenge
from CTFd.models import db, Challenges, Solves
from CTFd.utils.user import get_current_team, get_current_user
from .models import StorylineChallenge, SolutionDescription
from flask import request, jsonify
from datetime import datetime, timedelta

class StorylineChallengeType(BaseChallenge):
    id = "storyline"
    name = "storyline"
    templates = {
        "create": "/plugins/storyline_challenges/assets/create.html",
        "update": "/plugins/storyline_challenges/assets/update.html",
        "view": "/plugins/storyline_challenges/assets/view.html",
    }
    scripts = {
        "create": "/plugins/storyline_challenges/assets/create.js",
        "update": "/plugins/storyline_challenges/assets/update.js",
        "view": "/plugins/storyline_challenges/assets/view.js",
    }

    @staticmethod
    def create(request):
        data = request.form or request.get_json()
        challenge = Challenges(**data)
        db.session.add(challenge)
        db.session.commit()

        predecessor_id = data.get('predecessor_id')
        max_lifetime = data.get('max_lifetime')

        if predecessor_id == '':
            predecessor_id = None
        if max_lifetime == '':
            max_lifetime = None

        storyline_data = StorylineChallenge(
            id=challenge.id,
            predecessor_id=predecessor_id,
            max_lifetime=max_lifetime
        )
        db.session.add(storyline_data)
        db.session.commit()

        return challenge

    @staticmethod
    def read(challenge):
        challenge_data = challenge.__dict__.copy()
        storyline_data = StorylineChallenge.query.filter_by(id=challenge.id).first()
        if storyline_data:
            challenge_data['predecessor_id'] = storyline_data.predecessor_id
            challenge_data['max_lifetime'] = storyline_data.max_lifetime
        else:
            challenge_data['predecessor_id'] = None
            challenge_data['max_lifetime'] = None
        return challenge_data

    @staticmethod
    def update(challenge, request):
        data = request.form or request.get_json()

        for attr, value in data.items():
            if attr in ('predecessor_id', 'max_lifetime'):
                continue
            setattr(challenge, attr, value)

        storyline_data = StorylineChallenge.query.filter_by(id=challenge.id).first()
        if not storyline_data:
            storyline_data = StorylineChallenge(id=challenge.id)
            db.session.add(storyline_data)

        predecessor_id = data.get('predecessor_id')
        max_lifetime = data.get('max_lifetime')

        if predecessor_id == '':
            predecessor_id = None
        if max_lifetime == '':
            max_lifetime = None

        storyline_data.predecessor_id = predecessor_id
        storyline_data.max_lifetime = max_lifetime

        db.session.commit()
        return challenge

    @staticmethod
    def delete(challenge):
        StorylineChallenge.query.filter_by(id=challenge.id).delete()
        SolutionDescription.query.filter_by(challenge_id=challenge.id).delete()
        Challenges.query.filter_by(id=challenge.id).delete()
        db.session.commit()

    @staticmethod
    def attempt(challenge, request):
        data = request.form or request.get_json()
        submission = data["submission"].strip()
        flags = challenge.flags

        for flag in flags:
            if flag.compare(submission):
                return True, "Correct"
        return False, "Incorrect"

    @staticmethod
    def solve(user, team, challenge, request):
        from CTFd.plugins.challenges import get_chal_class
        super(StorylineChallengeType, StorylineChallengeType).solve(user, team, challenge, request)

        data = request.form or request.get_json()
        description = data.get('solution_description', '')

        if description:
            solution_desc = SolutionDescription(
                team_id=team.id,
                user_id=user.id,
                challenge_id=challenge.id,
                description=description
            )
            db.session.add(solution_desc)
            db.session.commit()

    @staticmethod
    def fail(user, team, challenge, request):
        from CTFd.plugins.challenges import get_chal_class
        return super(StorylineChallengeType, StorylineChallengeType).fail(user, team, challenge, request)
