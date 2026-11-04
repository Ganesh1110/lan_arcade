"""
College Quiz Show Trivia Game Module.
2–4 Player Competitive Trivia Game with Multi-Category Questions, Streaks, and Live Standings.
"""
import random
from config import paint

game_id = "quiz_show"
game_name = "Quiz Show"
min_players = 2
max_players = 4

TOTAL_ROUNDS = 8

QUESTION_BANK = [
    {
        "category": "💻 Computer Science",
        "question": "Which data structure operates on a First-In, First-Out (FIFO) principle?",
        "options": ["Stack", "Queue", "Binary Tree", "Heap"],
        "answer": "B",
        "fact": "Queues operate FIFO, whereas Stacks operate LIFO."
    },
    {
        "category": "💻 Computer Science",
        "question": "What is the average time complexity of quicksort?",
        "options": ["O(n)", "O(n log n)", "O(n^2)", "O(log n)"],
        "answer": "B",
        "fact": "Quicksort runs in O(n log n) average time and O(n^2) worst case."
    },
    {
        "category": "🌐 Networking & Web",
        "question": "Which port does standard HTTPS traffic use by default?",
        "options": ["80", "8080", "443", "22"],
        "answer": "C",
        "fact": "Port 443 is encrypted HTTPS, while Port 80 is unencrypted HTTP."
    },
    {
        "category": "🐧 Linux & OS",
        "question": "Which command is used to display currently running processes in Linux?",
        "options": ["ls", "top", "pwd", "chmod"],
        "answer": "B",
        "fact": "'top' or 'htop' shows live real-time process statistics."
    },
    {
        "category": "🚀 Tech & Hardware",
        "question": "What does CPU stand for?",
        "options": ["Central Processing Unit", "Computer Power Utility", "Core Program Unit", "Control Processor Universal"],
        "answer": "A",
        "fact": "The CPU is the central processing unit of a computer."
    },
    {
        "category": "🐍 Python",
        "question": "Which built-in Python function returns the length of a list or string?",
        "options": ["count()", "size()", "len()", "length()"],
        "answer": "C",
        "fact": "len() returns the number of items in a collection in O(1) time."
    },
    {
        "category": "🎮 Gaming & Culture",
        "question": "In what year was the original Nintendo Entertainment System (NES) released in North America?",
        "options": ["1981", "1985", "1990", "1983"],
        "answer": "B",
        "fact": "The NES launched in North America in 1985."
    },
    {
        "category": "🌍 Science",
        "question": "What is the most abundant gas in Earth's atmosphere?",
        "options": ["Oxygen", "Carbon Dioxide", "Nitrogen", "Argon"],
        "answer": "C",
        "fact": "Nitrogen makes up approximately 78% of Earth's atmosphere."
    },
    {
        "category": "💻 Computer Science",
        "question": "Who created the Git version control system and the Linux kernel?",
        "options": ["Steve Wozniak", "Linus Torvalds", "Dennis Ritchie", "Ken Thompson"],
        "answer": "B",
        "fact": "Linus Torvalds created both the Linux kernel (1991) and Git (2005)."
    },
    {
        "category": "🌐 Networking & Web",
        "question": "What does DNS stand for?",
        "options": ["Domain Name System", "Dynamic Network Server", "Digital Naming Standard", "Direct Node Serial"],
        "answer": "A",
        "fact": "DNS maps human-readable domain names to numerical IP addresses."
    },
    {
        "category": "🧠 AI & Data",
        "question": "What does the 'T' stand for in GPT (Generative Pre-trained Transformer)?",
        "options": ["Tensor", "Transformer", "Translator", "Technology"],
        "answer": "B",
        "fact": "Transformers were introduced by Google in the 2017 paper 'Attention Is All You Need'."
    },
    {
        "category": "🌍 General Knowledge",
        "question": "Which programming language was originally called 'Oak'?",
        "options": ["Python", "Java", "Ruby", "Kotlin"],
        "answer": "B",
        "fact": "James Gosling originally named Java after an oak tree outside his office."
    },
    {
        "category": "💻 Computer Science",
        "question": "Which layer of the OSI model does IP (Internet Protocol) operate on?",
        "options": ["Data Link (Layer 2)", "Network (Layer 3)", "Transport (Layer 4)", "Application (Layer 7)"],
        "answer": "B",
        "fact": "The Network layer (Layer 3) handles packet routing and logical IP addressing."
    },
    {
        "category": "🐍 Python",
        "question": "What is the output of bool([]) in Python?",
        "options": ["True", "False", "None", "TypeError"],
        "answer": "B",
        "fact": "Empty collections, None, and 0 evaluate to False in Python truth testing."
    },
    {
        "category": "🌐 Networking & Web",
        "question": "Which HTTP status code signifies 'Unauthorized'?",
        "options": ["200", "401", "403", "404"],
        "answer": "B",
        "fact": "HTTP 401 means Unauthorized (missing or invalid authentication credentials)."
    },
    {
        "category": "🚀 Tech & Hardware",
        "question": "Which type of memory is volatile and loses its contents when powered off?",
        "options": ["ROM", "NVMe SSD", "RAM", "Flash Memory"],
        "answer": "C",
        "fact": "RAM (Random Access Memory) requires continuous power to hold data."
    },
    {
        "category": "🐧 Linux & OS",
        "question": "What is PID 1 in modern Linux systems traditionally assigned to?",
        "options": ["bash", "systemd or init", "kernel", "sshd"],
        "answer": "B",
        "fact": "PID 1 is the first userspace process spawned during Linux boot."
    },
    {
        "category": "🧠 AI & Data",
        "question": "Which activation function outputs values strictly in the range (0, 1)?",
        "options": ["ReLU", "Sigmoid", "Tanh", "LeakyReLU"],
        "answer": "B",
        "fact": "The Sigmoid function maps real inputs to the range (0, 1)."
    }
]

QUESTIONS_PER_PLAYER = 3


def create_state(player_sessions):
    players = []
    scores = {}
    streaks = {}

    for s in player_sessions:
        pid = s["id"] if isinstance(s, dict) else s.player_id
        name = s["name"] if isinstance(s, dict) else s.name
        players.append({"id": pid, "name": name})
        scores[pid] = 0
        streaks[pid] = 0

    # Ensure perfectly balanced turns for all players (4 each for 2 players, 3 each for 3+ players)
    if len(players) == 2:
        total_q_count = TOTAL_ROUNDS
    else:
        total_q_count = len(players) * 3
    questions = list(QUESTION_BANK)
    random.shuffle(questions)
    # If more questions needed than bank, cycle through
    selected_questions = []
    while len(selected_questions) < total_q_count:
        for q in questions:
            selected_questions.append(q)
            if len(selected_questions) == total_q_count:
                break

    return {
        "players": players,
        "scores": scores,
        "streaks": streaks,
        "questions": selected_questions,
        "current_round": 0,
        "turn_index": 0,
        "winner": None,
        "log": ["🎤 Welcome to College Quiz Show! Earn points and build answer streaks!"]
    }


def current_player(state):
    players = state["players"]
    return players[state["turn_index"] % len(players)]["id"]


def view_for(state, player_id):
    p_data = next((p for p in state["players"] if p["id"] == player_id), None)
    curr_q = None
    if state["current_round"] < len(state["questions"]):
        q = state["questions"][state["current_round"]]
        # Sanitize question to prevent leaking answer key to clients
        curr_q = {
            "category": q["category"],
            "question": q["question"],
            "options": q["options"]
        }

    # Normalize scores with integer keys
    raw_scores = state.get("scores", {})
    scores = {int(k): v for k, v in raw_scores.items()} if isinstance(raw_scores, dict) else {}

    return {
        "player_id": player_id,
        "name": p_data["name"] if p_data else "Player",
        "players": state["players"],
        "scores": scores,
        "streaks": state["streaks"],
        "round_num": state["current_round"] + 1,
        "total_rounds": len(state["questions"]),
        "current_question": curr_q,
        "turn_id": current_player(state),
        "winner": state["winner"],
        "log": state["log"]
    }


def prompt_for(state_or_view, player_id):
    return "Enter your answer choice (A, B, C, or D)"


def parse_action(state_or_view, player_id, raw_input):
    choice = str(raw_input).strip().upper()
    if choice in {"A", "B", "C", "D"}:
        return True, choice
    return False, "Choice must be 'A', 'B', 'C', or 'D'."


def apply_action(state, player_id, choice):
    curr_p = next(p for p in state["players"] if p["id"] == player_id)
    p_name = curr_p["name"]

    curr_idx = state["current_round"]
    if curr_idx >= len(state["questions"]):
        return {"log": ["Quiz is completed."]}

    q_data = state["questions"][curr_idx]
    correct_ans = q_data["answer"]
    is_correct = (choice == correct_ans)
    log_entries = []

    if is_correct:
        streak = state["streaks"].get(player_id, 0) + 1
        state["streaks"][player_id] = streak
        pts = 100 + (streak - 1) * 25
        state["scores"][player_id] = state["scores"].get(player_id, 0) + pts
        streak_tag = f" 🔥 {streak}X STREAK!" if streak > 1 else ""
        log_entries.append(f"✅ {p_name} answered ({choice}) CORRECTLY! +{pts} pts!{streak_tag}")
    else:
        state["streaks"][player_id] = 0
        opt_idx = ord(correct_ans) - ord("A")
        correct_text = q_data["options"][opt_idx]
        log_entries.append(f"❌ {p_name} chose ({choice}). Incorrect! Correct was ({correct_ans}: {correct_text}).")

    # Advance to next round
    state["current_round"] += 1
    state["turn_index"] += 1

    # Check game over
    if state["current_round"] >= len(state["questions"]):
        max_score = max(state["scores"].values())
        winners = [p["name"] for p in state["players"] if state["scores"].get(p["id"], 0) == max_score]
        state["winner"] = winners
        log_entries.append(f"🏆 QUIZ COMPLETE! Winner: {', '.join(winners)} with {max_score} points!")

    state["log"].extend(log_entries)
    if len(state["log"]) > 8:
        state["log"] = state["log"][-8:]

    return {"log": log_entries}


def is_over(state):
    return state["winner"] is not None or state["current_round"] >= len(state["questions"])


def get_winner(state):
    if state["winner"]:
        return state["winner"]
    if is_over(state):
        max_sc = max(state["scores"].values())
        return [p["name"] for p in state["players"] if state["scores"].get(p["id"], 0) == max_sc]
    return []


def skip_player(state, player_id):
    if current_player(state) == player_id:
        state["current_round"] += 1
        state["turn_index"] += 1


def render_dashboard(view):
    players = view.get("players", [])
    raw_scores = view.get("scores", {})
    scores = {int(k): v for k, v in raw_scores.items()} if isinstance(raw_scores, dict) else {}
    streaks = view.get("streaks", {})
    q = view.get("current_question")
    round_num = view.get("round_num", 1)
    tot_rounds = view.get("total_rounds", TOTAL_ROUNDS)
    turn_id = view.get("turn_id")
    log = view.get("log", [])

    out = [
        paint("=" * 66, "1;36"),
        paint("             🎓 C O L L E G E   Q U I Z   S H O W 🎓", "1;36"),
        paint("=" * 66, "1;36"),
        ""
    ]

    # Scoreboard Standings
    out.append("  STANDINGS:")
    sorted_p = sorted(players, key=lambda p: scores.get(p["id"], 0), reverse=True)
    for idx, p in enumerate(sorted_p, 1):
        pid = p["id"]
        sc = scores.get(pid, 0)
        st = streaks.get(pid, 0)
        is_turn = (pid == turn_id)
        ptr = paint("▶", "1;32") if is_turn else " "
        streak_str = f"🔥 {st}" if st >= 2 else f"{st}"
        tag = " " + paint("◀ CURRENT TURN", "1;36") if is_turn else ""
        out.append(f"   {ptr} #{idx} {p['name']:<18} : {paint(str(sc), '1;33')} pts  (Streak: {streak_str}){tag}")
    out.append("")

    # Question Display Card
    if q:
        cat = q.get("category", "General")
        q_text = q.get("question", "")
        options = q.get("options", [])

        out.append("  " + paint("┌" + "─" * 62 + "┐", "1;36"))
        out.append(f"  │ Round {round_num}/{tot_rounds}  •  Category: {paint(cat, '1;33'):<46}│")
        out.append("  " + paint("├" + "─" * 62 + "┤", "1;36"))
        out.append(f"  │ {paint(q_text, '1;37'):<70}│")
        out.append("  " + paint("├" + "─" * 62 + "┤", "1;36"))

        labels = ["A", "B", "C", "D"]
        for lbl, opt in zip(labels, options):
            opt_line = f"  [{lbl}] {opt}"
            out.append(f"  │ {opt_line:<60} │")

        out.append("  " + paint("└" + "─" * 62 + "┘", "1;36"))

    if log:
        out.append("")
        out.append("  Recent Activity:")
        out.extend("   " + line for line in log[-3:])

    return "\n".join(out)


def render_final(view, message, winners):
    parts = [render_dashboard(view), ""]
    if winners:
        parts.append(paint(f"  🏆  QUIZ CHAMPION(S): {', '.join(winners)}!  🏆", "1;32"))
    else:
        parts.append(paint("  Quiz completed in a Tie!", "1;33"))
    return "\n".join(parts)
