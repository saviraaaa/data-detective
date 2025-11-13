from flask import Flask, request, redirect, url_for, render_template_string, session, send_file
import statistics, json, base64, io
from collections import Counter
from jinja2 import DictLoader
import qrcode
import pandas as pd
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

# Inisialisasi Flask
app = Flask(__name__)
app.secret_key = "data_detective_secret_2025"
MAX_ENTRIES = 10

# 🌈 Base Template (Pastel Theme)
BASE_HTML = '''
<!doctype html>
<html>
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>STATISTIKA - Data Detective</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
      :root{
        --bg: #FAFAFA;
        --header: #BCE4E8;
        --card: #FFF8E1;
        --btn: #A8E6CF;
        --text: #424242;
        --muted: #6b6b6b;
      }
      body { font-family: Inter, Arial, sans-serif; background: var(--bg); color: var(--text); margin:0; padding:20px; }
      .container { max-width: 1000px; margin: auto; }
      header { display:flex; justify-content:space-between; align-items:center; background: var(--header); padding:14px 18px; border-radius:12px; box-shadow: 0 2px 6px rgba(0,0,0,0.05); }
      .logo { display:flex; align-items:center; gap:10px; }
      .logo-mark { width:42px; height:42px; background:var(--btn); border-radius:8px; display:flex; align-items:center; justify-content:center; font-weight:700; color:#fff; }
      nav a { margin-left:12px; color:var(--text); text-decoration:none; font-weight:600; }
      .card { background: var(--card); padding:14px; border-radius:10px; margin-top:14px; box-shadow: 0 1px 4px rgba(0,0,0,0.03); }
      .row { display:flex; gap:12px; flex-wrap: wrap; }
      .col { flex:1; }
      input[type=number], input[type=text], input[type=file] { width:100%; padding:8px; border-radius:6px; border:1px solid #e6e6e6; }
      button { background:var(--btn); border:none; padding:8px 12px; border-radius:8px; cursor:pointer; font-weight:600; }
      small { color: var(--muted); }
      footer { margin-top:18px; text-align:center; color:var(--muted); }
      .muted { color: var(--muted); font-size:0.9rem; }
    </style>
  </head>
  <body>
    <div class="container">
      <header>
        <div class="logo">
          <div class="logo-mark">DD</div>
          <div>
            <div style="font-weight:800">Data Detective</div>
            <small>STATISTIKA — pembelajaran & latihan</small>
          </div>
        </div>
        <nav>
          <a href="{{ url_for('index') }}">Home</a>
          <a href="{{ url_for('stats') }}">Stats</a>
          <a href="{{ url_for('games') }}">Games</a>
          <a href="{{ url_for('about') }}">About</a>
        </nav>
      </header>
      {% block content %}{% endblock %}
      <footer><small>Created for Week 1 - Foundation · Data Detective</small></footer>
    </div>
  </body>
</html>
'''

# Daftarkan base template
app.jinja_loader = DictLoader({'base.html': BASE_HTML})

# 🔹 Helper
def get_data():
    return session.get('data', [])

def save_data(lst):
    cleaned = []
    for v in lst:
        try:
            cleaned.append(float(v))
        except Exception:
            continue
    session['data'] = cleaned[:MAX_ENTRIES]

def calc_mean(lst):
    return statistics.mean(lst) if lst else None

def calc_median(lst):
    return statistics.median(lst) if lst else None

def calc_mode(lst):
    if not lst: return None
    c = Counter(lst)
    max_count = max(c.values())
    return sorted([k for k, v in c.items() if v == max_count])

# ===============================
# 📄 Halaman
# ===============================
INDEX_HTML = '''
{% extends "base.html" %}
{% block content %}
<div class="card">
  <h2>📁 Import Data</h2>
  <form method="POST" action="{{ url_for('import_data') }}" enctype="multipart/form-data">
    <div class="row">
      <div class="col"><input type="file" name="file" accept=".csv,.json" required></div>
      <div class="col" style="flex:0.3"><button type="submit">Import</button></div>
    </div>
    <p class="muted">CSV: kolom pertama atau kolom bernama 'nilai' akan dibaca. JSON: array langsung atau {"data":[...]}.</p>
  </form>

  {% if data %}
  <hr>
  <p>Data saat ini: {{ data }}</p>
  <form method="POST" action="{{ url_for('clear_data') }}">
    <button type="submit" style="background:#FFABAB;">Kosongkan</button>
  </form>
  {% else %}
  <small>Belum ada data yang diimpor.</small>
  {% endif %}
</div>

<div class="card">
  <h2>📈 Analisis Cepat</h2>
  {% if data %}
    <ul>
      <li>Rata-rata (Mean): {{ mean }}</li>
      <li>Median: {{ median }}</li>
      <li>Modus: {{ mode }}</li>
    </ul>
    <a href="{{ url_for('stats') }}"><button>Lihat Visualisasi</button></a>
  {% else %}
    <small>Impor data untuk melihat hasil analisis.</small>
  {% endif %}
</div>
{% endblock %}
'''

STATS_HTML = '''
{% extends "base.html" %}
{% block content %}
<div class="card">
  <h2>📊 Visualisasi Data</h2>
  {% if not data %}
    <small>Belum ada data untuk divisualisasikan.</small>
  {% else %}
    <div style="display:flex; gap:8px; margin-bottom:8px;">
      <a href="{{ url_for('stats', chart='bar') }}"><button>Bar / Histogram</button></a>
      <a href="{{ url_for('stats', chart='scatter') }}"><button>Scatter</button></a>
      <a href="{{ url_for('report') }}"><button>Download Report</button></a>
    </div>

    <canvas id="chart" width="800" height="400"></canvas>
    <script>
      const rawData = {{ data | tojson }};
      const chartType = "{{ chart_type }}";
      const ctx = document.getElementById('chart');

      if (chartType === 'scatter') {
        const points = rawData.map((v, i) => ({ x: i+1, y: v }));
        new Chart(ctx, {
          type: 'scatter',
          data: { datasets: [{ label: 'Scatter (index vs value)', data: points, pointRadius: 6 }] },
          options: { scales: { x: { title: { display: true, text: 'Index' } }, y: { title: { display: true, text: 'Value' } } } }
        });
      } else {
        const freqs = {};
        rawData.forEach(v => freqs[v] = (freqs[v] || 0) + 1);
        new Chart(ctx, {
          type: 'bar',
          data: { labels: Object.keys(freqs), datasets: [{ label: 'Frekuensi nilai', data: Object.values(freqs), borderWidth: 1 }] },
          options: { scales: { y: { beginAtZero: true } } }
        });
      }
    </script>
  {% endif %}
</div>
{% endblock %}
'''

GAMES_HTML = '''
{% extends "base.html" %}
{% block content %}
<div class="card">
  <h2>🎯 Tebak Rata-rata</h2>
  {% if data %}
  <p>Data: {{ data }}</p>
  <form method="POST" action="{{ url_for('check_guess') }}">
    <input type="number" name="guess" step="any" placeholder="Tebak rata-rata..." required>
    <button type="submit">Cek Jawaban</button>
  </form>
  {% else %}
  <small>Tambahkan data terlebih dahulu di menu Home.</small>
  {% endif %}
</div>
{% endblock %}
'''

RESULT_HTML = '''
{% extends "base.html" %}
{% block content %}
<div class="card">
  <h2>🔍 Hasil Tebakan</h2>
  <p>Jawabanmu: {{ guess }}</p>
  <p>Rata-rata yang benar: {{ mean }}</p>
  <h3>{{ message }}</h3>
  <a href="{{ url_for('games') }}"><button>Main lagi</button></a>
</div>
{% endblock %}
'''

ABOUT_HTML = '''
{% extends "base.html" %}
{% block content %}
<div class="card" style="text-align:center">
  <h2>👩‍💻 Biodata Kelompok</h2>
  <p>Kelompok Statistika - Data Detective</p>
  <img src="data:image/png;base64,{{ qr_img }}" alt="QR Biodata" width="220">
  <p><small>Scan QR untuk melihat detail biodata kelompok</small></p>
</div>
{% endblock %}
'''

# ===============================
# 🚀 ROUTES
# ===============================
@app.route('/')
def index():
    data = get_data()
    return render_template_string(INDEX_HTML, data=data, mean=calc_mean(data),
                                  median=calc_median(data), mode=calc_mode(data))

@app.route('/import', methods=['POST'])
def import_data():
    file = request.files.get('file')
    if not file:
        return redirect(url_for('index'))

    filename = file.filename.lower()
    data = []
    try:
        if filename.endswith('.csv'):
            df = pd.read_csv(file)
            numeric_cols = df.select_dtypes(include='number').columns.tolist()
            col = numeric_cols[0] if numeric_cols else df.columns[0]
            data = df[col].dropna().tolist()
        elif filename.endswith('.json'):
            file.stream.seek(0)
            content = json.load(file)
            if isinstance(content, dict) and 'data' in content:
                data = content['data']
            elif isinstance(content, list):
                data = content
    except Exception:
        data = []

    save_data(data)
    return redirect(url_for('index'))

@app.route('/clear', methods=['POST'])
def clear_data():
    save_data([])
    return redirect(url_for('index'))

@app.route('/stats')
def stats():
    chart_type = request.args.get('chart', 'bar')
    data = get_data()
    return render_template_string(STATS_HTML, data=data, chart_type=chart_type)

@app.route('/games')
def games():
    data = get_data()
    return render_template_string(GAMES_HTML, data=data)

@app.route('/check', methods=['POST'])
def check_guess():
    guess = request.form.get('guess', type=float)
    data = get_data()
    mean = calc_mean(data)
    if mean is None:
        message = "Belum ada data untuk dibandingkan."
    else:
        message = "Benar banget! 🎉" if abs(guess - mean) < 0.001 else "Belum tepat, coba lagi!"
    return render_template_string(RESULT_HTML, guess=guess, mean=mean, message=message)

@app.route('/report')
def report():
    data = get_data()
    mean, median, mode = calc_mean(data), calc_median(data), calc_mode(data)

    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    c.setFont("Helvetica-Bold", 18)
    c.drawString(80, 800, "Data Detective - Report")
    c.setFont("Helvetica", 12)
    c.drawString(80, 770, f"Jumlah data: {len(data)}")
    c.drawString(80, 750, f"Data (truncated): {str(data[:50])}")
    c.drawString(80, 730, f"Mean: {mean}")
    c.drawString(80, 710, f"Median: {median}")
    c.drawString(80, 690, f"Mode: {mode}")
    c.drawString(80, 650, "Generated by Data Detective")
    c.showPage()
    c.save()

    buffer.seek(0)
    return send_file(buffer, as_attachment=True, download_name="data_report.pdf", mimetype='application/pdf')

@app.route('/biodata')
def biodata():
    members = [
        {"nama": "Yunita Wulandari", "nim": "24-032", "role": "Backend"},
        {"nama": "Aditio Danar Banjebat", "nim": "24-036", "role": "Frontend"},
        {"nama": "Savira Rizky Ruwaidah Santoso Puteri", "nim": "24-080", "role": "Content"}
    ]

    group_info = {
        "nama_kelompok": "Statistika",
        "aplikasi": "Data Detective",
        "anggota": members,
        "institusi": "Pendidikan Matematika, FKIP, Universitas Jember",
        "repository": "https://github.com/saviraaaa/data-detective"
    }

    qr_data = json.dumps(group_info, ensure_ascii=False, indent=2)
    qr = qrcode.make(qr_data)
    buf = io.BytesIO()
    qr.save(buf, format='PNG')
    qr_b64 = base64.b64encode(buf.getvalue()).decode('utf-8')
    return render_template_string(ABOUT_HTML, qr_img=qr_b64)

@app.route('/about')
def about():
    return redirect(url_for('biodata'))

# Jalankan Aplikasi
if __name__ == '__main__':
    app.run(debug=True)