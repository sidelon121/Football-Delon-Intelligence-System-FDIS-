"""
FDIS REST API Routes
JSON API endpoints for data operations.
"""
from dotenv import load_dotenv
import os
import json
from re import match
from flask import Blueprint, redirect, request, jsonify, current_app, send_file, render_template, url_for
from werkzeug.utils import secure_filename
from app.models import Team, Player, Match, UploadHistory
from app import db
from app.engine.statistics import get_match_analysis, get_player_overview
from app.engine.nlg import generate_match_summary, generate_player_analysis
from app.utils.pdf_exporter import create_pdf, safe_text
import tempfile
from app.engine.visualizations import chart_match_comparison, chart_match_donut_stats
from app.engine.visualizations import chart_player_radar
from app.utils.chart_exporter import save_chart_as_image
import plotly.graph_objects as go
import json
import requests
import tempfile
from app.engine.ai_engine import generate_ai_match_analysis
from app.engine.statistics import get_match_analysis
from flask import send_file
from app.models import Team, Player
from app.engine.statistics import get_team_comparison, get_player_comparison


load_dotenv()

api_bp = Blueprint('api', __name__)

def get_logo_path(url):
    try:
        r = requests.get(url, timeout=5)
        if r.status_code == 200:
            tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
            tmp.write(r.content)
            tmp.close()
            return tmp.name
    except:
        return None


# ========================
# MATCH PDF
# ========================
def clean_text(text):
    lines = text.split('\n')
    unique = []
    for line in lines:
        if line.strip() not in unique:
            unique.append(line.strip())
    return '\n'.join(unique)

@api_bp.route('/export/pdf/match/<int:match_id>')
def export_match_pdf(match_id):
    from app.engine.statistics import get_match_analysis
    from app.engine.ai_engine import generate_ai_match_analysis
    from app.utils.chart_exporter import save_chart_as_image
    import plotly.graph_objects as go
    
    data = get_match_analysis(match_id)
    if not data:
        return "Match not found", 404

    pdf = create_pdf()
    match = data['match']
    metrics = data.get('metrics', {})

    home = match['home_team']['name']
    away = match['away_team']['name']

    # 🏆 HEADER
    pdf.section_header("MATCH REPORT")
    pdf.set_font("Arial", "", 10)
    pdf.cell(0, 6, f"{match.get('league','-')} | {match.get('date','-')} | {match.get('venue','-')}", ln=True, align="C")
    pdf.ln(5)
    # ⚽ SCORE & SCORERS
    pdf.set_font("Arial", "B", 24)
    pdf.cell(85, 15, home, align="R")
    pdf.set_text_color(102, 126, 234) # Warna biru PDF
    pdf.cell(20, 15, f"{match['home_goals']} - {match['away_goals']}", align="C")
    pdf.set_text_color(0, 0, 0)
    pdf.cell(85, 15, away, align="L")
    pdf.set_font("Arial", 'I', 10)
    pdf.ln(12)

    pdf.set_font("Arial", "I", 9)
    pdf.set_text_color(100, 100, 100) # Warna abu-abu halus
    pdf.cell(85, 5, f"{match['home_goalscorers'] or '-'}", align="R")
    pdf.cell(20, 5, "", align="C")
    pdf.cell(85, 5, f"{match['away_goalscorers'] or '-'}", ln=True, align="L")
    pdf.ln(15)
    # 📊 STATS BARS
    pdf.section_title("Match Statistics")
    for key, m in metrics.items():
        if isinstance(m, dict):
            pdf.stat_vs_bar(m.get('label', key), m.get('home', 0), m.get('away', 0))

    # ==========================================
    # VISUAL MATCH STATS (FINAL COMPACT VERSION)
    # ==========================================
    pdf.add_page()
    pdf.section_title("Visual Match Stats")

    circle_metrics = data.get("circle_metrics", [])
    y = pdf.get_y() + 4

    for m in circle_metrics:

        # =========================
        # AUTO PAGE BREAK
        # =========================
        if y + 68 > 270:
            pdf.add_page()
            y = 10
        # =========================
        # METRIC TITLE
        # =========================
        pdf.set_xy(8, y + 2)
        pdf.set_font("Arial", "B", 11)
        pdf.cell(190, 6, safe_text(m["label"]), align="C")

        # =========================
        # TEAM NAMES
        # =========================
        pdf.set_font("Arial", "B", 8)

        pdf.set_xy(40, y + 8)
        pdf.cell(60, 4, safe_text(home), align="C")

        pdf.set_xy(135, y + 8)
        pdf.cell(60, 4, safe_text(away), align="C")

        # =========================
        # HOME CHART
        # =========================
        fig_home = go.Figure(data=[go.Pie(
            labels=m["labels"],
            values=m["home_values"],
            hole=0.4,
            marker_colors=["#3d08fd", "#fa0909", "#77868D"],
            textposition="auto", 
            texttemplate="<b>%{value}</b><br>(%{percent})", 
            textinfo='value+percent',
            textfont=dict(size=30, color='black')
        )])

        fig_home.update_layout(
            width=280,
            height=240,
            showlegend=True,
            legend=dict(
                x=1.0,
                y=0.82,
                font=dict(size=8)
            ),
            annotations=[dict(
                text=f"{m['home_values'][0]}/{sum(m['home_values'])}", # Contoh: 551/620
                x=0.5, y=0.5, 
                font=dict(size=30, color='black'), 
                showarrow=False
            )],
            margin=dict(t=5, b=5, l=5, r=55),
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)'
        )

        home_img = save_chart_as_image(fig_home)
        pdf.image(home_img, x=15, y=y + 7, w=60)

        # =========================
        # AWAY CHART
        # =========================
        fig_away = go.Figure(data=[go.Pie(
            labels=m["labels"],
            values=m["away_values"],
            hole=0.4,
            marker_colors=["#9b59b6", "#fa0909", "#77868D"],
            textposition="auto", 
            texttemplate="<b>%{value}</b><br>(%{percent})", 
            textinfo='value+percent',
            textfont=dict(size=30, color='black')
        )])

        fig_away.update_layout(
            width=280,
            height=240,
            showlegend=True,
            legend=dict(
                x=1.0,
                y=0.82,
                font=dict(size=8)
            ),
            annotations=[dict(
                text=f"{m['away_values'][0]}/{sum(m['away_values']  )}", # Contoh: 551/620
                x=0.5, y=0.5, 
                font=dict(size=30, color='black'), 
                showarrow=False
            )],
            margin=dict(t=5, b=5, l=5, r=55),
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)'
        )

        away_img = save_chart_as_image(fig_away)
        pdf.image(away_img, x=113, y=y + 7, w=60)

        # =========================
        # NEXT CARD POSITION
        # =========================
        y += 40

    # =========================
    # MOVE CURSOR AFTER CHARTS
    # =========================
    pdf.set_y(y + 4)
        
    # 📝 ANALYSIS
    summary = generate_ai_match_analysis(data)
    if summary:
        pdf.section_header("Analysis & Insights")
        for p in summary.split("\n\n"):
            pdf.section_text(p)
    
    temp = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    pdf.output(temp.name)

    filename = f"Match_{home}_vs_{away}.pdf".replace(" ", "_")
    return send_file(temp.name, as_attachment=True, download_name=filename)


@api_bp.route('/export/pdf/player/<int:player_id>')
def export_player_pdf(player_id):
    from app.engine.statistics import get_player_overview
    from app.engine.ai_engine import generate_ai_player_analysis
    from app.utils.chart_exporter import save_chart_as_image
    import plotly.graph_objects as go

    data = get_player_overview(player_id)
    if not data:
        return "Player not found", 404

    pdf = create_pdf()
    player = data['player']

    # 🧾 HEADER
    pdf.section_header(f"PLAYER PROFILE: {player['name']}")
    
    # BASIC INFO TABLE
    pdf.section_title("Personal Information")
    pdf.draw_table(
        ["Position", "Team", "Matches", "Avg Rating"],
        [[player.get('position', '-'), player.get('team_name', '-'), data.get('matches_played', 0), data.get('avg_rating', 0)]],
        [45, 65, 40, 40]
    )

    # 📊 PERFORMANCE CHART (Radar)
    metrics = ["Goals/90", "Assists/90", "Shot Acc (%)", "Pass Acc (%)", "Dribble Acc (%)"]
    values = [
        data.get('goals_per_90', 0) * 10, # Scaling for visibility
        data.get('assists_per_90', 0) * 10,
        data.get('shot_accuracy', 0),
        data.get('avg_pass_accuracy', 0),
        data.get('dribble_success_rate', 0)
    ]
    
    fig = go.Figure(data=[go.Scatterpolar(r=values, theta=metrics, fill='toself', marker_color='#4807fd')])
    fig.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 100])), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
    img_path = save_chart_as_image(fig)

    pdf.section_title("Performance Analysis")
    pdf.image(img_path, x=15, y=pdf.get_y(), w=180)
    pdf.ln(100)

    # 🤖 AI ANALYSIS
    analysis = generate_ai_player_analysis(data)
    if analysis:
        pdf.section_header("Tactical Evaluation")
        for p in analysis.split("\n\n"):
            pdf.section_text(p)

    temp = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    pdf.output(temp.name)
    filename = f"Player_{player['name']}.pdf".replace(" ", "_")
    return send_file(temp.name, as_attachment=True, download_name=filename)

# ─── Upload Endpoints ─────────────────────────────────────────────
def allowed_file(filename):
    if not filename:
        return False
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'csv', 'xlsx', 'xls'}


@api_bp.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'success': False, 'error': 'No file provided'}), 400

    file = request.files['file']

    if file.filename == '':
        return jsonify({'success': False, 'error': 'No file selected'}), 400

    if not allowed_file(file.filename):
        return jsonify({'success': False, 'error': 'File type not allowed'}), 400

    upload_dir = current_app.config.get('UPLOAD_FOLDER', 'uploads')

    if not os.path.exists(upload_dir):
        os.makedirs(upload_dir)

    filename = secure_filename(file.filename)
    filepath = os.path.join(upload_dir, filename)

    file.save(filepath)

    from app.ingestion.csv_handler import process_uploaded_file

    result = process_uploaded_file(filepath, filename)

    return redirect(url_for('main.dashboard'))
    

@api_bp.route('/manual-entry', methods=['POST'])
def manual_entry():
    """Handle manual match data entry."""
    from app.ingestion.manual_handler import process_manual_match
    data = request.get_json() or request.form.to_dict()

    if not data:
        return jsonify({'success': False, 'error': 'No data provided'}), 400

    result = process_manual_match(data)
    return jsonify(result)


@api_bp.route('/manual-player', methods=['POST'])
def manual_player_entry():
    """Handle manual player stats entry."""
    from app.ingestion.manual_handler import process_manual_player_stats
    data = request.get_json() or request.form.to_dict()

    if not data:
        return jsonify({'success': False, 'error': 'No data provided'}), 400

    result = process_manual_player_stats(data)
    return jsonify(result)


@api_bp.route('/fetch-api', methods=['POST'])
def fetch_api():
    """Trigger API-Football data fetch."""
    data = request.get_json() or request.form.to_dict()
    league_id = data.get('league_id')
    season = data.get('season')

    if not league_id or not season:
        return jsonify({'success': False, 'error': 'league_id and season are required'}), 400

    from app.ingestion.api_handler import APIFootballClient
    client = APIFootballClient()
    result = client.fetch_and_store_fixtures(
        league_id=int(league_id),
        season=int(season),
        last=data.get('last')
    )
    return jsonify(result)


# ─── Statistics Endpoints ─────────────────────────────────────────

def serialize(obj):
    if isinstance(obj, list):
        return [serialize(i) for i in obj]
    elif isinstance(obj, dict):
        return {k: serialize(v) for k, v in obj.items()}
    elif hasattr(obj, "to_dict"):
        return obj.to_dict()
    else:
        return obj

@api_bp.route('/stats/team/<int:team_id>')
def team_stats(team_id):
    """Get team statistics."""
    from app.engine.statistics import get_team_overview
    from app.utils.serializers import serialize
    data = get_team_overview(team_id)
    if not data:
        return jsonify({'error': 'Team not found'}), 404
    return jsonify(serialize(data))


@api_bp.route('/stats/player/<int:player_id>')
def player_stats(player_id):
    """Get player statistics."""
    from app.engine.statistics import get_player_overview
    data = get_player_overview(player_id)
    if not data:
        return jsonify({'error': 'Player not found'}), 404
    return jsonify(serialize(data))


@api_bp.route('/stats/match/<int:match_id>')
def match_stats(match_id):
    """Get match statistics."""
    from app.engine.statistics import get_match_analysis
    data = get_match_analysis(match_id)
    if not data:
        return jsonify({'error': 'Match not found'}), 404
    return jsonify(serialize(data))



@api_bp.route('/stats/league-table')
def league_table():
    """Get league table standings."""
    from app.engine.statistics import get_league_table
    league = request.args.get('league')
    season = request.args.get('season')
    table = get_league_table(league=league, season=season)
    return jsonify(table)


# ─── Chart Endpoints ──────────────────────────────────────────────

@api_bp.route('/chart/team-radar/<int:team_id>')
def chart_team_radar(team_id):
    """Get team radar chart JSON."""
    from app.engine.visualizations import chart_team_radar
    chart = chart_team_radar(team_id)
    if not chart:
        return jsonify({'error': 'No data'}), 404
    return jsonify(chart)


@api_bp.route('/chart/team-form/<int:team_id>')
def chart_team_form(team_id):
    """Get team form chart JSON."""
    from app.engine.visualizations import chart_team_form
    chart = chart_team_form(team_id)
    if not chart:
        return jsonify({'error': 'No data'}), 404
    return jsonify(chart)


@api_bp.route('/chart/match/<int:match_id>')
def chart_match(match_id):
    """Get match comparison chart JSON."""
    from app.engine.visualizations import chart_match_comparison
    chart = chart_match_comparison(match_id)
    if not chart:
        return jsonify({'error': 'No data'}), 404
    return jsonify(chart)


@api_bp.route('/chart/player-radar/<int:player_id>')
def chart_player_radar(player_id):
    """Get player radar chart JSON."""
    from app.engine.visualizations import chart_player_radar
    chart = chart_player_radar(player_id)
    if not chart:
        return jsonify({'error': 'No data'}), 404
    return jsonify(chart)


# ─── Analysis Endpoints ──────────────────────────────────────────
import json
import plotly
import json
import plotly
from flask import render_template
# Pastikan fungsi-fungsi ini sudah di-import di bagian atas file Anda:
# from app.engine.statistics import get_match_analysis
# from app.engine.ai_summary import generate_ai_match_analysis, generate_match_summary
# from app.engine.visualisasi import chart_match_donut_stats

@api_bp.route('/match/<int:match_id>')
def match_detail(match_id):
    # 1. Ambil data match
    data = get_match_analysis(match_id)

    if not data:
        return "Match not found", 404

    # 2. 🔥 LOGIKA AI SUMMARY (Milik Anda)
    summary_text = generate_ai_match_analysis(data)

    # Fallback kalau AI gagal
    if not summary_text or "failed" in summary_text.lower():
        summary_text = generate_match_summary(match_id)

    # Biar rapi di HTML
    if summary_text:
        summary_text = summary_text.replace(". ", ".\n\n")

    print("FINAL WEB SUMMARY:", summary_text)
    
    # 3. 🔥 LOGIKA GRAFIK BULAT (DONUT)
    # Memanggil fungsi yang mengembalikan banyak dictionary (bukan 1 chart)
    donut_charts_dict = chart_match_donut_stats(match_id)

    # Konversi ke String JSON yang aman menggunakan PlotlyJSONEncoder
    charts_json = json.dumps(donut_charts_dict, cls=plotly.utils.PlotlyJSONEncoder) if donut_charts_dict else "{}"

    # 4. Kirim semua data ke Template
    return render_template(
        "match_detail.html",
        summary_text=summary_text,
        match=data['match'],
        data=data,
        charts_json=charts_json,
    )

@api_bp.route('/analysis/team/<int:team_id>')
def analysis_team(team_id):
    """Get auto-generated team analysis text."""
    from app.engine.nlg import generate_team_analysis
    text = generate_team_analysis(team_id)
    return jsonify({'analysis': text})


@api_bp.route('/analysis/player/<int:player_id>')
def analysis_player(player_id):
    """Get auto-generated player analysis text."""
    from app.engine.nlg import generate_player_analysis
    text = generate_player_analysis(player_id)
    return jsonify({'analysis': text})


# ─── Comparison Endpoint ─────────────────────────────────────────
@api_bp.route('/export/pdf/compare')
def export_compare_pdf():
    from app.engine.statistics import get_team_comparison, get_player_comparison
    from app.engine.ai_engine import generate_ai_comparison_analysis
    from app.utils.chart_exporter import save_chart_as_image
    import plotly.graph_objects as go
    import tempfile

    compare_type = request.args.get('type', 'team')
    id1 = request.args.get('id1', type=int)
    id2 = request.args.get('id2', type=int)

    if not id1 or not id2:
        return "Invalid request", 400

    if compare_type == "team":
        data = get_team_comparison(id1, id2)
    else:
        data = get_player_comparison(id1, id2)

    if not data:
        return "Comparison data not found", 404

    # Safe meta access with fallback
    meta = data.get('meta', {}) if isinstance(data, dict) else {}
    if not isinstance(meta, dict):
        meta = {}
    data['meta'] = meta

    if not meta.get('name1'):
        obj1 = Team.query.get(id1) if compare_type == "team" else Player.query.get(id1)
        meta['name1'] = obj1.name if obj1 else "Item 1"
    if not meta.get('name2'):
        obj2 = Team.query.get(id2) if compare_type == "team" else Player.query.get(id2)
        meta['name2'] = obj2.name if obj2 else "Item 2"

    name1 = meta['name1']
    name2 = meta['name2']

    chart_data = data.get('chart_data', {})

    if compare_type == "team":
        # Create Chart for PDF
        fig = go.Figure(data=[
            go.Bar(name=name1, x=chart_data.get('labels', []), y=chart_data.get('team1', []), marker_color='#667eea'),
            go.Bar(name=name2, x=chart_data.get('labels', []), y=chart_data.get('team2', []), marker_color='#764ba2')
        ])
        fig.update_layout(barmode='group', paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
    else:
        # Radar Chart for PDF
        fig = go.Figure()
        fig.add_trace(go.Scatterpolar(r=chart_data.get('player1', []), theta=chart_data.get('labels', []), fill='toself', name=name1))
        fig.add_trace(go.Scatterpolar(r=chart_data.get('player2', []), theta=chart_data.get('labels', []), fill='toself', name=name2))
        fig.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 100])), showlegend=True)

    img_path = save_chart_as_image(fig)
    pdf = create_pdf()

    # HEADER
    pdf.section_header(f"COMPARISON: {name1} VS {name2}")
    
    # CHART
    pdf.section_title("Visual Performance Analysis")
    pdf.image(img_path, x=15, y=pdf.get_y(), w=180)
    pdf.ln(95) # space for image

    # STATS BARS
    pdf.section_title("Statistical Comparison")
    for m in data.get('metrics', []):
        pdf.stat_vs_bar(m.get('label', ''), m.get('t1', 0), m.get('t2', 0))

    # AI ANALYSIS
    ai_text = generate_ai_comparison_analysis(data, compare_type)
    if ai_text:
        pdf.section_header("Tactical Insights")
        for p in ai_text.split("\n\n"):
            pdf.section_text(p)

    temp = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    pdf.output(temp.name)

    filename = f"Compare_{name1}_vs_{name2}.pdf".replace(" ", "_")
    return send_file(temp.name, as_attachment=True, download_name=filename)

def clean_for_json(obj):
    if isinstance(obj, dict):
        return {k: clean_for_json(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [clean_for_json(i) for i in obj]
    elif hasattr(obj, "to_dict"):
        return obj.to_dict()
    else:
        return obj

@api_bp.route('/compare')
def compare_page():
    compare_type = request.args.get('type', 'team')
    id1 = request.args.get('id1', type=int)
    id2 = request.args.get('id2', type=int)

    from app.models import Team, Player
    from app.engine.statistics import get_team_comparison, get_player_comparison
    import json

    # ✅ AMBIL DATA DARI DB → CONVERT KE LIST AMAN
    teams = [{"id": t.id, "name": t.name} for t in Team.query.all()]
    players = [{"id": p.id, "name": p.name} for p in Player.query.all()]

    data = None

    # ✅ AMBIL DATA PERBANDINGAN (PAKAI ENGINE, BUKAN MODEL LANGSUNG!)
    if id1 and id2:
        if compare_type == "team":
            data = get_team_comparison(id1, id2)
        else:
            data = get_player_comparison(id1, id2)

        # Tambahkan nama
        if data:
            obj1 = Team.query.get(id1) if compare_type == "team" else Player.query.get(id1)
            obj2 = Team.query.get(id2) if compare_type == "team" else Player.query.get(id2)

            data["meta"] = {
                "name1": obj1.name if obj1 else "Item 1",
                "name2": obj2.name if obj2 else "Item 2"
            }

    return render_template(
        "compare.html",
        teams=teams,
        players=players,
        data=data,
        data_json=json.dumps(data) if data else "null"
    )
# ─── Export Endpoints ─────────────────────────────────────────────


@api_bp.route('/export/pdf/team/<int:team_id>')
def export_team_pdf(team_id):
    from app.engine.statistics import get_team_overview
    from app.engine.ai_engine import generate_ai_team_analysis
    from app.utils.chart_exporter import save_chart_as_image
    import plotly.graph_objects as go

    data = get_team_overview(team_id)
    if not data:
        return "Team not found", 404

    pdf = create_pdf()
    team = data['team']

    # 🧾 HEADER
    pdf.section_header(f"CLUB REPORT: {team['name']}")
    
    # TEAM OVERVIEW
    pdf.section_title("Seasonal Performance")
    pdf.draw_table(
        ["League", "MP", "W-D-L", "Win Rate", "Points"],
        [[team.get('league', '-'), data.get('matches_played', 0), f"{data.get('wins')}-{data.get('draws')}-{data.get('losses')}", f"{data.get('win_rate')}%", data.get('points', 0)]],
        [60, 20, 40, 35, 35]
    )

    # 📊 PERFORMANCE DONUT
    fig = go.Figure(data=[go.Pie(
        labels=["Win", "Draw", "Loss"],
        values=[data.get('wins', 0), data.get('draws', 0), data.get('losses', 0)],
        hole=0.4,
        marker=dict(colors=["#43e97b", "#8b949e", "#f85149"])
    )])
    fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', margin=dict(t=0, b=0, l=0, r=0))
    img_path = save_chart_as_image(fig)

    pdf.section_title("Match Results Distribution")
    pdf.image(img_path, x=60, y=pdf.get_y(), w=90)
    pdf.ln(85)

    # STAT BARS
    pdf.section_title("Technical Metrics")
    pdf.stat_vs_bar("Goals For vs Against", data.get('goals_for', 0), data.get('goals_against', 0))
    pdf.stat_vs_bar("Avg Possession (%)", data.get('avg_possession', 0), 100 - data.get('avg_possession', 0))

    # 🤖 AI ANALYSIS
    analysis = generate_ai_team_analysis(data)
    if analysis:
        pdf.section_header("Tactical Analysis")
        for p in analysis.split("\n\n"):
            pdf.section_text(p)

    temp = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    pdf.output(temp.name)
    filename = f"Team_{team['name']}.pdf".replace(" ", "_")
    return send_file(temp.name, as_attachment=True, download_name=filename)


# ─── Utility Endpoints ───────────────────────────────────────────

@api_bp.route('/teams')
def list_teams():
    """List all teams."""
    teams = Team.query.order_by(Team.name).all()
    return jsonify([t.to_dict() for t in teams])


@api_bp.route('/players')
def list_players():
    """List all players."""
    players = Player.query.order_by(Player.name).all()
    return jsonify([p.to_dict() for p in players])


@api_bp.route('/matches')
def list_matches():
    """List all matches."""
    matches = Match.query.order_by(Match.date.desc()).all()
    return jsonify([m.to_dict() for m in matches])


@api_bp.route('/upload-history')
def upload_history():
    """Get upload history."""
    history = UploadHistory.query.order_by(UploadHistory.upload_date.desc()).limit(50).all()
    return jsonify([h.to_dict() for h in history])
