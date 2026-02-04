<!DOCTYPE html>
<html lang="pt-br">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Dashboard - Sniper Pro</title>
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css">
    <style>
        body { background-color: #0a0a0a; color: #f0f0f0; }
        .card-stats { background: #161616; border: 1px solid #333; border-radius: 15px; padding: 20px; }
        .status-on { color: #28a745; font-weight: bold; }
        .status-off { color: #dc3545; font-weight: bold; }
        .table-dark { --bs-table-bg: #161616; }
    </style>
</head>
<body>
    <div class="container py-5">
        <div class="d-flex justify-content-between align-items-center mb-5">
            <div>
                <h1 class="fw-bold m-0 text-primary">🎯 Sniper Mix</h1>
                <p class="text-muted small">ID: {{ wallet[:6] }}...{{ wallet[-4:] }}</p>
            </div>
            <form action="/toggle_bot" method="post">
                {% if bot.status == 'OFF' %}
                    <input type="hidden" name="status" value="ON">
                    <button type="submit" class="btn btn-success px-4 fw-bold shadow">ATIVAR</button>
                {% else %}
                    <input type="hidden" name="status" value="OFF">
                    <button type="submit" class="btn btn-danger px-4 fw-bold shadow">PARAR</button>
                {% endif %}
            </form>
        </div>

        <div class="row g-4 mb-5 text-center">
            <div class="col-md-4"><div class="card-stats">Saldo POL<h2 class="text-info">{{ pol }}</h2></div></div>
            <div class="col-md-4"><div class="card-stats">Banca USDC<h2 class="text-primary">{{ usdc }}</h2></div></div>
            <div class="col-md-4"><div class="card-stats">Motor<h2 class="{{ 'status-on' if bot.status == 'ON' else 'status-off' }}">{{ bot.status }}</h2></div></div>
        </div>

        <div class="card-stats">
            <h5 class="mb-4">📜 Logs (Ciclo 5 min)</h5>
            <div class="table-responsive">
                <table class="table table-dark table-hover border-secondary">
                    <thead><tr><th>Hora</th><th>Mercado</th><th>Ação</th><th>Resultado</th></tr></thead>
                    <tbody>
                        {% for item in historico %}
                        <tr>
                            <td>{{ item.data }}</td>
                            <td>{{ item.mercado }}</td>
                            <td class="text-uppercase">{{ item.lado }}</td>
                            <td><span class="badge bg-primary">{{ item.resultado }}</span></td>
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>
            </div>
        </div>
    </div>
</body>
</html>