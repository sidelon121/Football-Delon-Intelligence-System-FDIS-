import os
from groq import Groq

# ========================
# INIT CLIENT (GLOBAL)
# ========================
api_key = os.getenv("GROQ_API_KEY")

if not api_key:
    raise ValueError("❌ GROQ_API_KEY tidak ditemukan")

client = Groq(api_key=api_key)


# ========================
# HELPER FORMAT METRICS
# ========================
def format_metrics(metrics):
    if not metrics:
        return "No stats available"

    lines = []
    for m in metrics.values():
        label = m.get('label', '')
        home = m.get('home', 0)
        away = m.get('away', 0)

        lines.append(f"{label}: {home} vs {away}")

    return "\n".join(lines)


# ========================
# MATCH AI
# ========================
def generate_ai_match_analysis(data):
    try:
        if not data:
            return None

        match = data['match']
        metrics = format_metrics(data.get('metrics', {}))

        home = match['home_team']['name']
        away = match['away_team']['name']

        prompt = f"""
You are a world-class football analyst.
Before you explain, carefully review and analyze this football match data.


Match: {home} vs {away}
Score: {match['home_goals']} - {match['away_goals']}
data: {match['date']}
league: {match['league']}
venue: {match['venue']}
goalscorers: {match['home_goalscorers']} vs {match['away_goalscorers']}
Stats:
{metrics}

Explain in detail and specifically:
- Explain all available statistics
- Who won and why
- Who lost and why
- Who deserved to win
- Tactical differences
- Why one team won despite unfavorable statistics (if any)
- Why one team lost despite favorable statistics (if any)
- Why the team lost
- Why the team won
- What were the strengths and weaknesses of both teams
- Key insights

Write 2-3 short paragraphs.
"""

        res = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7
        )

        return res.choices[0].message.content.strip()

    except Exception as e:
        print("❌ AI MATCH ERROR:", e)
        return None


# ========================
# PLAYER AI
# ========================
def generate_ai_player_analysis(data):
    try:
        if not data:
            return None

        player = data.get('player', {})

        prompt = f"""
Analyze this football player:
Before you explain, carefully review and analyze this.


Name: {player.get('name')}
Team: {player.get('team_name')}
Matches: {data.get('matches_played')}
Goals: {data.get('total_goals')}
Assists: {data.get('total_assists')}
Rating: {data.get('avg_rating')}

Explain:
- Strengths
- Weaknesses
- Performance insight

Write clearly in 2-3 paragraphs.
"""

        res = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7
        )

        return res.choices[0].message.content.strip()

    except Exception as e:
        print("❌ AI PLAYER ERROR:", e)
        return None


# ========================
# TEAM AI
# ========================
def generate_ai_team_analysis(data):
    try:
        if not data:
            return None

        team = data.get('team', {})

        prompt = f"""
Analyze this football team:
Before you explain, carefully review and analyze this.

data: {team.get('name')}
league: {team.get('league')}
venue: {team.get('venue')}

Stats: {data.get('metrics', {})}

Team: {team.get('name')}
Matches: {data.get('matches_played')}
Wins: {data.get('wins')}
Losses: {data.get('losses')}
Win Rate: {data.get('win_rate')}%

Explain:
- Play style
- Strengths
- Weaknesses
- Tactical insight

Write in 2-3 paragraphs.
"""

        res = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7
        )

        return res.choices[0].message.content.strip()

    except Exception as e:
        print("❌ AI TEAM ERROR:", e)
        return None
    
def generate_ai_comparison_analysis(data, compare_type="team"):
    try:
        from groq import Groq
        import os

        client = Groq(api_key=os.getenv("GROQ_API_KEY"))

        meta = data.get('meta', {}) if isinstance(data, dict) else {}
        name1 = meta.get('name1', 'Item 1')
        name2 = meta.get('name2', 'Item 2')

        # Build a readable stats summary from metrics
        metrics_text = ""
        for m in data.get('metrics', []):
            metrics_text += f"{m.get('label','')}: {m.get('t1',0)} vs {m.get('t2',0)}\n"

        if compare_type == "team":
            prompt = f"""
Compare these two football teams:

Team A: {name1}
Team B: {name2}

Stats:
{metrics_text}

Explain:
- Who is stronger and why
- Tactical differences
- Strength & weaknesses
- Who would likely win and why

Write 2-3 paragraphs.
"""

        else:
            prompt = f"""
Compare these two players:

Player A: {name1}
Player B: {name2}

Stats:
{metrics_text}

Explain:
- Who is better and why
- Strengths & weaknesses
- Playing style difference

Write 2-3 paragraphs.
"""

        res = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}]
        )

        return res.choices[0].message.content

    except Exception as e:
        print("AI COMPARE ERROR:", e)
        return None