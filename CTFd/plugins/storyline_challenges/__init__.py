from CTFd.plugins import register_plugin_assets_directory
from CTFd.plugins.challenges import CHALLENGE_CLASSES
from .models import StorylineChallenge, SolutionDescription
from .routes import storyline_blueprint
from .challenge_type import StorylineChallengeType
from .utils import init_db

def load(app):
    init_db()

    CHALLENGE_CLASSES["storyline"] = StorylineChallengeType

    app.register_blueprint(storyline_blueprint)

    register_plugin_assets_directory(
        app, base_path="/plugins/storyline_challenges/assets/"
    )

    app.logger.info("Storyline Challenges plugin loaded successfully")
