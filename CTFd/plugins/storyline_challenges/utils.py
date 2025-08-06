from CTFd.models import db
from .models import StorylineChallenge, SolutionDescription

def init_db():
    """Initialize database tables for storyline challenges"""
    db.create_all()

def get_challenge_dependencies():
    """Get a dictionary mapping challenge IDs to their dependencies"""
    dependencies = {}
    storyline_challenges = StorylineChallenge.query.all()

    for sc in storyline_challenges:
        dependencies[sc.id] = {
            'predecessor_id': sc.predecessor_id,
            'max_lifetime': sc.max_lifetime
        }

    return dependencies

def calculate_storyline_stats():
    """Calculate statistics about the storyline graph"""
    from CTFd.models import Challenges

    total_challenges = Challenges.query.count()
    storyline_challenges = StorylineChallenge.query.count()
    root_challenges = StorylineChallenge.query.filter_by(predecessor_id=None).count()
    timed_challenges = StorylineChallenge.query.filter(StorylineChallenge.max_lifetime.isnot(None)).count()

    return {
        'total_challenges': total_challenges,
        'storyline_challenges': storyline_challenges,
        'root_challenges': root_challenges,
        'timed_challenges': timed_challenges,
        'regular_challenges': total_challenges - storyline_challenges
    }
