from CTFd.models import db, Challenges, Solves
from CTFd.utils import get_config
from .models import StorylineChallenge, SolutionDescription
from .utils import get_unlocked_challenges_for_team
from datetime import datetime, timedelta

class StorylineManager:
    """Core business logic for managing storyline challenges"""

    @staticmethod
    def unlock_challenges_for_team(team_id, solved_challenge_id):
        """Unlock child challenges when a challenge is solved"""
        child_challenges = StorylineChallenge.query.filter_by(predecessor_id=solved_challenge_id).all()

        unlocked_challenges = []
        for child in child_challenges:
            unlocked_challenges.append({
                'challenge_id': child.id,
                'max_lifetime': child.max_lifetime,
                'unlocked_at': datetime.utcnow()
            })

        return unlocked_challenges

    @staticmethod
    def check_challenge_accessibility(team_id, challenge_id):
        """Check if a team can access a specific challenge"""
        storyline_data = StorylineChallenge.query.filter_by(id=challenge_id).first()

        if not storyline_data or storyline_data.predecessor_id is None:
            return True, None

        predecessor_solve = Solves.query.filter_by(
            team_id=team_id,
            challenge_id=storyline_data.predecessor_id
        ).first()

        if not predecessor_solve:
            return False, "Predecessor challenge not solved"

        if storyline_data.max_lifetime:
            expiry_time = predecessor_solve.date + timedelta(minutes=storyline_data.max_lifetime)
            if datetime.utcnow() > expiry_time:
                return False, "Challenge has expired"

        return True, None

    @staticmethod
    def get_storyline_progress(team_id):
        """Get detailed progress through the storyline for a team"""
        from .routes import get_unlocked_challenges_for_team

        unlocked = get_unlocked_challenges_for_team(team_id)
        solved = db.session.query(Solves.challenge_id).filter_by(team_id=team_id).all()
        solved_ids = {s.challenge_id for s in solved}

        total_challenges = Challenges.query.count()
        storyline_challenges = StorylineChallenge.query.count()

        return {
            'unlocked_count': len(unlocked),
            'solved_count': len(solved_ids),
            'total_challenges': total_challenges,
            'storyline_challenges': storyline_challenges,
            'unlocked_challenges': list(unlocked),
            'solved_challenges': list(solved_ids)
        }

    @staticmethod
    def validate_storyline_integrity():
        """Validate the integrity of the storyline graph"""
        issues = []

        storyline_challenges = StorylineChallenge.query.all()
        challenge_ids = {sc.id for sc in storyline_challenges}

        for sc in storyline_challenges:
            if sc.predecessor_id and sc.predecessor_id not in challenge_ids:
                issues.append(f"Challenge {sc.id} references non-existent predecessor {sc.predecessor_id}")

            if sc.max_lifetime and sc.max_lifetime <= 0:
                issues.append(f"Challenge {sc.id} has invalid max_lifetime: {sc.max_lifetime}")

        return len(issues) == 0, issues
