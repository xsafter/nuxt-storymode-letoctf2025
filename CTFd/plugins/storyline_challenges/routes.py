from flask import Blueprint, request, jsonify, render_template
from CTFd.models import db, Challenges, Solves, Teams
from CTFd.utils.user import get_current_team, get_current_user, is_admin
from CTFd.utils.decorators import authed_only, admins_only
from .models import StorylineChallenge, SolutionDescription
from datetime import datetime, timedelta
from sqlalchemy import and_

storyline_blueprint = Blueprint('storyline', __name__, url_prefix='/storyline')

def get_unlocked_challenges_for_team(team_id):
    """Get all challenges unlocked for a specific team based on their solves and time constraints"""
    team_solves = db.session.query(
        Solves.challenge_id,
        Solves.date
    ).filter_by(team_id=team_id).all()

    solved_challenges = {solve.challenge_id: solve.date for solve in team_solves}

    challenges = db.session.query(
        Challenges.id,
        StorylineChallenge.predecessor_id,
        StorylineChallenge.max_lifetime
    ).outerjoin(StorylineChallenge, Challenges.id == StorylineChallenge.id).all()

    unlocked = set()

    for challenge in challenges:
        if challenge.predecessor_id is None:
            unlocked.add(challenge.id)
        elif challenge.predecessor_id in solved_challenges:
            parent_solve_time = solved_challenges[challenge.predecessor_id]

            if challenge.max_lifetime:
                expiry_time = parent_solve_time + timedelta(minutes=challenge.max_lifetime)
                if datetime.utcnow() <= expiry_time:
                    unlocked.add(challenge.id)
            else:
                unlocked.add(challenge.id)

    return unlocked

def validate_challenge_graph():
    """Validate that the challenge graph doesn't have cycles"""
    challenges = db.session.query(
        StorylineChallenge.id,
        StorylineChallenge.predecessor_id
    ).all()

    graph = {}
    for challenge in challenges:
        if challenge.id not in graph:
            graph[challenge.id] = []
        if challenge.predecessor_id:
            if challenge.predecessor_id not in graph:
                graph[challenge.predecessor_id] = []
            graph[challenge.predecessor_id].append(challenge.id)

    def has_cycle(node, visited, rec_stack):
        visited[node] = True
        rec_stack[node] = True

        for neighbor in graph.get(node, []):
            if not visited.get(neighbor, False):
                if has_cycle(neighbor, visited, rec_stack):
                    return True
            elif rec_stack.get(neighbor, False):
                return True

        rec_stack[node] = False
        return False

    visited = {}
    rec_stack = {}

    for node in graph:
        if not visited.get(node, False):
            if has_cycle(node, visited, rec_stack):
                return False

    return True

@storyline_blueprint.route('/admin/graph', methods=['GET'])
@admins_only
def admin_graph():
    challenges = db.session.query(
        Challenges.id,
        Challenges.name,
        Challenges.category,
        Challenges.value,
        StorylineChallenge.predecessor_id,
        StorylineChallenge.max_lifetime
    ).outerjoin(StorylineChallenge, Challenges.id == StorylineChallenge.id).all()

    nodes = []
    edges = []

    for challenge in challenges:
        nodes.append({
            'id': challenge.id,
            'name': challenge.name,
            'category': challenge.category,
            'value': challenge.value,
            'max_lifetime': challenge.max_lifetime
        })

        if challenge.predecessor_id:
            edges.append({
                'from': challenge.predecessor_id,
                'to': challenge.id,
                'max_lifetime': challenge.max_lifetime
            })

    return jsonify({
        'nodes': nodes,
        'edges': edges
    })

@storyline_blueprint.route('/player/graph', methods=['GET'])
@authed_only
def player_graph():
    team = get_current_team()
    if not team:
        return jsonify({'error': 'Team not found'}), 404

    team_solves = db.session.query(
        Solves.challenge_id,
        Solves.date
    ).filter_by(team_id=team.id).all()

    solved_challenges = {solve.challenge_id: solve.date for solve in team_solves}

    challenges = db.session.query(
        Challenges.id,
        Challenges.name,
        Challenges.category,
        Challenges.value,
        StorylineChallenge.predecessor_id,
        StorylineChallenge.max_lifetime
    ).outerjoin(StorylineChallenge, Challenges.id == StorylineChallenge.id).all()

    unlocked_challenges = set()
    expired_challenges = set()

    for challenge in challenges:
        if challenge.predecessor_id is None:
            unlocked_challenges.add(challenge.id)
        elif challenge.predecessor_id in solved_challenges:
            parent_solve_time = solved_challenges[challenge.predecessor_id]

            if challenge.max_lifetime:
                expiry_time = parent_solve_time + timedelta(minutes=challenge.max_lifetime)
                if datetime.utcnow() > expiry_time:
                    expired_challenges.add(challenge.id)
                else:
                    unlocked_challenges.add(challenge.id)
            else:
                unlocked_challenges.add(challenge.id)

    nodes = []
    edges = []

    for challenge in challenges:
        if challenge.id in unlocked_challenges or challenge.id in solved_challenges:
            status = 'solved' if challenge.id in solved_challenges else 'unlocked'
            if challenge.id in expired_challenges:
                status = 'expired'

            time_remaining = None
            if challenge.max_lifetime and challenge.predecessor_id in solved_challenges and status == 'unlocked':
                parent_solve_time = solved_challenges[challenge.predecessor_id]
                expiry_time = parent_solve_time + timedelta(minutes=challenge.max_lifetime)
                time_remaining = int((expiry_time - datetime.utcnow()).total_seconds() / 60)
                time_remaining = max(0, time_remaining)

            nodes.append({
                'id': challenge.id,
                'name': challenge.name,
                'category': challenge.category,
                'value': challenge.value,
                'status': status,
                'time_remaining': time_remaining
            })

            if challenge.predecessor_id and (challenge.predecessor_id in unlocked_challenges or challenge.predecessor_id in solved_challenges):
                edges.append({
                    'from': challenge.predecessor_id,
                    'to': challenge.id
                })

    return jsonify({
        'nodes': nodes,
        'edges': edges
    })

@storyline_blueprint.route('/admin/challenges', methods=['GET'])
@admins_only
def get_challenges_for_dropdown():
    challenges = Challenges.query.all()
    return jsonify([{
        'id': c.id,
        'name': c.name,
        'category': c.category
    } for c in challenges])

@storyline_blueprint.route('/solution-description', methods=['POST'])
@authed_only
def submit_solution_description():
    data = request.get_json()
    team = get_current_team()
    user = get_current_user()

    if not team or not user:
        return jsonify({'error': 'Authentication required'}), 401

    challenge_id = data.get('challenge_id')
    description = data.get('description', '').strip()

    if not challenge_id or not description:
        return jsonify({'error': 'Challenge ID and description required'}), 400

    solve = Solves.query.filter_by(
        team_id=team.id,
        challenge_id=challenge_id
    ).first()

    if not solve:
        return jsonify({'error': 'Challenge not solved'}), 400

    existing_desc = SolutionDescription.query.filter_by(
        team_id=team.id,
        challenge_id=challenge_id
    ).first()

    if existing_desc:
        existing_desc.description = description
        existing_desc.submitted_at = datetime.utcnow()
    else:
        solution_desc = SolutionDescription(
            team_id=team.id,
            user_id=user.id,
            challenge_id=challenge_id,
            description=description
        )
        db.session.add(solution_desc)

    db.session.commit()
    return jsonify({'success': True})

@storyline_blueprint.route('/admin/solutions', methods=['GET'])
@admins_only
def get_solution_descriptions():
    descriptions = db.session.query(
        SolutionDescription.id,
        SolutionDescription.description,
        SolutionDescription.submitted_at,
        Teams.name.label('team_name'),
        Challenges.name.label('challenge_name')
    ).join(Teams).join(Challenges).all()

    return jsonify([{
        'id': desc.id,
        'team_name': desc.team_name,
        'challenge_name': desc.challenge_name,
        'description': desc.description,
        'submitted_at': desc.submitted_at.isoformat()
    } for desc in descriptions])

@storyline_blueprint.route('/admin/validate-graph', methods=['GET'])
@admins_only
def validate_graph():
    """Validate the challenge graph for cycles and orphaned challenges"""
    is_valid = validate_challenge_graph()

    challenges = db.session.query(
        Challenges.id,
        Challenges.name,
        StorylineChallenge.predecessor_id
    ).outerjoin(StorylineChallenge, Challenges.id == StorylineChallenge.id).all()

    root_challenges = [c for c in challenges if c.predecessor_id is None]
    orphaned_challenges = []

    if len(root_challenges) == 0:
        orphaned_challenges = [c for c in challenges]

    return jsonify({
        'is_valid': is_valid,
        'has_cycles': not is_valid,
        'root_challenges_count': len(root_challenges),
        'orphaned_challenges': [{'id': c.id, 'name': c.name} for c in orphaned_challenges]
    })

@storyline_blueprint.route('/team/<int:team_id>/unlocked', methods=['GET'])
@admins_only
def get_team_unlocked_challenges(team_id):
    """Get unlocked challenges for a specific team (admin view)"""
    unlocked = get_unlocked_challenges_for_team(team_id)

    challenges = db.session.query(
        Challenges.id,
        Challenges.name,
        Challenges.category
    ).filter(Challenges.id.in_(unlocked)).all()

    return jsonify([{
        'id': c.id,
        'name': c.name,
        'category': c.category
    } for c in challenges])

@storyline_blueprint.route('/admin/progress', methods=['GET'])
@admins_only
def get_teams_progress():
    """Get progress overview for all teams through the storyline"""
    teams = Teams.query.all()
    progress_data = []

    for team in teams:
        unlocked = get_unlocked_challenges_for_team(team.id)
        solved = db.session.query(Solves.challenge_id).filter_by(team_id=team.id).all()
        solved_ids = {s.challenge_id for s in solved}

        total_challenges = Challenges.query.count()

        progress_data.append({
            'team_id': team.id,
            'team_name': team.name,
            'unlocked_count': len(unlocked),
            'solved_count': len(solved_ids),
            'total_challenges': total_challenges,
            'progress_percentage': round((len(solved_ids) / total_challenges) * 100, 2) if total_challenges > 0 else 0
        })

    return jsonify(progress_data)
