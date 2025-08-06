# CTFd Storyline Challenges Plugin

## Backend Implementation

This plugin extends CTFd to support storyline-based challenges that form a directed graph structure with dependencies and time constraints.

### Core Features

#### 1. Database Models
- **StorylineChallenge**: Extends challenges with predecessor relationships and time limits
- **SolutionDescription**: Stores team write-ups for solved challenges

#### 2. Challenge Dependencies
- Challenges can have predecessor requirements
- Child challenges unlock when predecessors are solved
- Supports branching storylines with multiple paths

#### 3. Time-Limited Side Quests
- Optional `max_lifetime` field for challenges
- Challenges expire if not solved within time limit after predecessor
- Automatic expiry checking on graph requests

#### 4. Solution Write-ups
- Teams must provide solution descriptions after solving
- Admin interface to review all team solutions
- Timestamped submissions with team/user tracking

### API Endpoints

#### Admin Endpoints
- `GET /storyline/admin/graph` - Full challenge graph visualization
- `GET /storyline/admin/challenges` - Available challenges for dropdowns
- `GET /storyline/admin/solutions` - All team solution descriptions
- `GET /storyline/admin/validate-graph` - Graph integrity validation
- `GET /storyline/admin/progress` - Team progress overview
- `GET /storyline/team/{id}/unlocked` - Team-specific unlocked challenges

#### Player Endpoints
- `GET /storyline/player/graph` - Team's visible challenge graph
- `POST /storyline/solution-description` - Submit solution write-up

### Backend Components

#### Core Classes
- **StorylineChallengeType**: Custom challenge type implementation
- **StorylineManager**: Business logic for challenge unlocking
- **Database Models**: Extended challenge and solution storage

#### Key Features
- Cycle detection for graph validation
- Team progress tracking
- Challenge accessibility verification
- Automatic challenge unlocking on solve
- Time-based expiry handling

### Frontend Stubs

Template stubs created for:
- Challenge creation form with predecessor/lifetime fields
- Challenge update form with existing values
- Challenge view with graph visualization
- Solution description modal

JavaScript stubs for:
- Admin dropdown population
- Graph data fetching and rendering
- Solution submission handling

### Installation

1. Place plugin in `CTFd/plugins/storyline_challenges/`
2. Restart CTFd server
3. Plugin automatically creates database tables
4. Use "storyline" challenge type in admin interface

### Database Schema

```sql
storyline_challenges:
  - id (FK to challenges.id)
  - predecessor_id (FK to challenges.id, nullable)
  - max_lifetime (integer minutes, nullable)

solution_descriptions:
  - id (primary key)
  - team_id (FK to teams.id)
  - user_id (FK to users.id) 
  - challenge_id (FK to challenges.id)
  - description (text)
  - submitted_at (datetime)
```

### Usage

1. Create challenges with type "storyline"
2. Set predecessor and time limit fields
3. Challenges automatically unlock based on solves
4. Teams see filtered graph based on progress
5. Solution descriptions collected on solve
