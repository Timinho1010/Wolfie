from flask import Flask, render_template, request, jsonify, session
import random

app = Flask(__name__)
app.secret_key = "your_secret_key"  # Set a secret key for session management

# Game Data
game_state = {
    "players": [],
    "eliminated": [],
    "wolves": [],
    "sheep": [],
    "round": 1,
    "votes": {},
    "final_two": [],
    "points": {},
    "recruited": set()  # Track recruited wolves
}

usernames = [f"Player {i+1}" for i in range(10)]  # Username for 10 players

@app.route('/')
def index():
    return render_template('index.html', usernames=usernames)

@app.route('/start_game', methods=['POST'])
def start_game():
    random.shuffle(usernames)
    game_state["players"] = usernames
    game_state["wolves"] = [usernames[0]]  # 1st player is the wolf
    game_state["sheep"] = usernames[1:]
    game_state["points"] = {username: 0 for username in usernames}

    session["current_player"] = usernames[0]  # Player 1 starts

    return jsonify({"status": "Game started!"})

@app.route('/vote', methods=['POST'])
def vote():
    vote_data = request.get_json()
    player = vote_data["player"]
    voted_player = vote_data["voted_player"]

    # Store the vote
    game_state["votes"][player] = voted_player

    # Eliminate the player with the most votes if all have voted
    if len(game_state["votes"]) == len(game_state["players"]):
        return eliminate_player()

    return jsonify({"status": "Vote recorded"})

def eliminate_player():
    # Count votes and find the most-voted player
    vote_count = {}
    for vote in game_state["votes"].values():
        if vote not in vote_count:
            vote_count[vote] = 0
        vote_count[vote] += 1

    # Find the player with the maximum votes
    max_votes = max(vote_count.values())
    eliminated_players = [player for player, count in vote_count.items() if count == max_votes]

    # If there's a tie, eliminate both players
    for player in eliminated_players:
        game_state["eliminated"].append(player)
        game_state["players"].remove(player)
    
    # Reset the votes for the next round
    game_state["votes"] = {}

    if len(game_state["players"]) <= 2:
        game_state["final_two"] = game_state["players"]
        return jsonify({"status": "Game over, Final two players!"})

    return jsonify({"status": "Round over. Players eliminated!"})

@app.route('/recruit', methods=['POST'])
def recruit():
    if game_state["round"] in [2, 4, 6] and len(game_state["wolves"]) == 1:
        recruit_target = random.choice(game_state["sheep"])
        game_state["wolves"].append(recruit_target)
        game_state["sheep"].remove(recruit_target)
        game_state["recruited"].add(recruit_target)
        return jsonify({"status": f"{recruit_target} has become a wolf!"})

    return jsonify({"status": "Not a recruitment round or wolf already eliminated!"})

@app.route('/final_vote', methods=['POST'])
def final_vote():
    vote_data = request.get_json()
    player = vote_data["player"]
    vote = vote_data["vote"]

    # Assign points based on the final vote
    if vote == "sheep":
        if game_state["final_two"][0] == "sheep" and game_state["final_two"][1] == "sheep":
            game_state["points"][game_state["final_two"][0]] += 10
            game_state["points"][game_state["final_two"][1]] += 10
        else:
            if "wolf" in vote_data["votes"]:
                # Assign points based on the game rules
                game_state["points"][game_state["final_two"][0]] += 50
            return jsonify({"status": "Game finished!"})

    return jsonify({"status": "Votes recorded"})

if __name__ == "__main__":
    app.run(debug=True)
