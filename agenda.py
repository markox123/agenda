from flask import Flask, request, render_template_string, redirect, url_for, session, flash
import json, os, datetime, threading, time
import uuid
# import pywhatkit  # pip install pywhatkit

app = Flask(__name__)
app.secret_key = 'sua_chave_secreta'

import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
USUARIOS_ARQ = os.path.join(BASE_DIR, "usuarios.json")
AGENDA_ARQ = os.path.join(BASE_DIR, "agendamentos.json")

def carregar_usuarios():
    if os.path.exists(USUARIOS_ARQ):
        with open(USUARIOS_ARQ, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def salvar_usuarios(usuarios):
    with open(USUARIOS_ARQ, "w", encoding="utf-8") as f:
        json.dump(usuarios, f, ensure_ascii=False, indent=2)

def carregar_agenda():
    if os.path.exists(AGENDA_ARQ):
        with open(AGENDA_ARQ, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def salvar_agenda(agenda):
    with open(AGENDA_ARQ, "w", encoding="utf-8") as f:
        json.dump(agenda, f, ensure_ascii=False, indent=2)

usuarios = carregar_usuarios()
agenda = carregar_agenda()

# Garante que todos os agendamentos tenham um campo 'id'
alterado = False
for ag in agenda:
    if 'id' not in ag:
        ag['id'] = str(uuid.uuid4())
        alterado = True
if alterado:
    salvar_agenda(agenda)

# --- Corrige horários inválidos em agendamentos.json ---
ARQ = "agendamentos.json"

if os.path.exists(ARQ):
    with open(ARQ, "r", encoding="utf-8") as f:
        agenda = json.load(f)

    alterado = False
    hoje = datetime.datetime.now().strftime("%d/%m/%Y")
    for ag in agenda:
        horario = ag.get("horario", "")
        # Se só tem hora (ex: "10:30"), corrige para "hoje HH:MM"
        if len(horario) == 5 and ":" in horario:
            ag["horario"] = f"{hoje} {horario}"
            alterado = True

    if alterado:
        with open(ARQ, "w", encoding="utf-8") as f:
            json.dump(agenda, f, ensure_ascii=False, indent=2)
        print("Horários corrigidos!")
    else:
        print("Nenhum horário para corrigir.")
else:
    print("Arquivo agendamentos.json não encontrado.")

# --- Notificação WhatsApp ---
# def notificador():
#     while True:
#         agora = datetime.datetime.now()
#         for ag in agenda:
#             if ag.get('notificado'):
#                 continue
#             try:
#                 horario = datetime.datetime.strptime(ag['horario'], "%d/%m/%Y %H:%M")
#             except Exception as e:
#                 print(f"Agendamento ignorado por formato inválido: {ag}")
#                 continue
#             if 0 < (horario - agora).total_seconds() <= 900:  # 900s = 15min
#                 try:
#                     pywhatkit.sendwhatmsg_instantly(
#                         ag['telefone'], 
#                         f"Olá {ag['nome']}, seu horário está marcado para {ag['horario']}! Faltam 15 minutos.",
#                         wait_time=10, tab_close=True
#                     )
#                     ag['notificado'] = True
#                     salvar_agenda(agenda)
#                 except Exception as e:
#                     print("Erro ao notificar:", e)
#         time.sleep(60)

# threading.Thread(target=notificador, daemon=True).start()

# --- Notificação para o usuário logado ---
def verificar_notificacoes():
    notificacoes = []
    agora = datetime.datetime.now()
    for ag in agenda:
        if ag.get('status') != 'Finalizado' and not ag.get('notificado'):
            try:
                horario = datetime.datetime.strptime(ag['horario'], "%d/%m/%Y %H:%M")
            except Exception:
                continue
            if 0 < (horario - agora).total_seconds() <= 900:  # 15 minutos
                notificacoes.append(f"Agendamento de {ag['nome']} às {ag['horario']} está próximo!")
                ag['notificado'] = True
    if notificacoes:
        salvar_agenda(agenda)
    return notificacoes

# --- Rotas de login/cadastro ---
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        usuario = request.form['usuario']
        senha = request.form['senha']
        if usuario in usuarios and usuarios[usuario]['senha'] == senha:
            session['usuario'] = usuario
            return redirect(url_for('home'))
        flash('Usuário ou senha inválidos')
    return render_template_string("""
    <!DOCTYPE html>
    <html lang="pt-br">
    <head>
        <meta charset="UTF-8">
        <title>Login - Studio de Beleza</title>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
        <link href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.css" rel="stylesheet">
        <style>
            body { background: linear-gradient(120deg, #f8fafc 60%, #e0e7ef 100%); }
            .login-card { border-radius: 1.5rem; box-shadow: 0 0 24px #0001; }
            .logo { height: 60px; max-width: 100%; object-fit: contain; }
            .form-control, .btn { border-radius: 0.7rem; }
            .btn-primary { background: #0d6efd; border: none; }
            .btn-primary:hover { background: #0b5ed7; }
            .form-label { font-weight: 500; }
            @media (max-width: 576px) {
                .login-card { padding: 1rem; }
                .logo { height: 40px !important; }
            }
        </style>
    </head>
    <body>
    <div class="container py-5">
        <div class="row justify-content-center">
            <div class="col-lg-5 col-md-7">
                <div class="card login-card p-4">
                    <div class="text-center mb-4">
                        <img src="/static/logo-net30.png" alt="Studio de Beleza" class="logo mb-2">
                        <h2 class="mb-0 text-primary" style="font-weight:700;letter-spacing:1px;">Studio de Beleza</h2>
                        <div class="text-muted small">Agendamento de Sobrancelhas, Cílios, Unhas, Cabelos e mais</div>
                    </div>
                    {% with messages = get_flashed_messages() %}
                      {% if messages %}
                        <div class="alert alert-danger text-center py-2">
                          {{ messages[0] }}
                        </div>
                      {% endif %}
                    {% endwith %}
                    <form method="post" autocomplete="off">
                        <div class="mb-3">
                            <label class="form-label">Usuário</label>
                            <input name="usuario" class="form-control" placeholder="Digite seu usuário" required autofocus>
                        </div>
                        <div class="mb-3">
                            <label class="form-label">Senha</label>
                            <input name="senha" type="password" class="form-control" placeholder="Digite sua senha" required>
                        </div>
                        <div class="d-grid mb-2">
                            <button type="submit" class="btn btn-primary btn-lg">
                                <i class="bi bi-door-open"></i> Entrar
                            </button>
                        </div>
                        <div class="text-center mt-2">
                            <a href="/cadastro" class="small text-decoration-none text-primary">
                                <i class="bi bi-person-plus"></i> Criar conta
                            </a>
                        </div>
                    </form>
                </div>
            </div>
        </div>
    </div>
    </body>
    </html>
    """)

@app.route('/cadastro', methods=['GET', 'POST'])
def cadastro():
    if request.method == 'POST':
        usuario = request.form['usuario']
        senha = request.form['senha']
        if usuario in usuarios:
            flash('Usuário já existe')
        else:
            usuarios[usuario] = {'senha': senha}
            salvar_usuarios(usuarios)
            flash('Cadastro realizado! Faça login.')
            return redirect(url_for('login'))
    return render_template_string("""
    <form method="post">
        <input name="usuario" placeholder="Usuário" required>
        <input name="senha" type="password" placeholder="Senha" required>
        <button type="submit">Cadastrar</button>
    </form>
    """)

@app.route('/logout')
def logout():
    session.pop('usuario', None)
    return redirect(url_for('login'))

# --- Home protegida ---
@app.route('/', methods=['GET', 'POST'])
def home():
    if 'usuario' not in session:
        return redirect(url_for('login'))
    if request.method == 'POST':
        nome = request.form.get('nome')
        horario = request.form.get('horario')  # formato: dd/mm/yyyy HH:MM
        telefone = request.form.get('telefone')  # formato: +5511999999999
        if nome and horario and telefone:
            try:
                datetime.datetime.strptime(horario, "%d/%m/%Y %H:%M")
            except ValueError:
                flash('Formato de data/hora inválido! Use dd/mm/yyyy HH:MM')
                return redirect(url_for('home'))
            agenda.append({
                'id': str(uuid.uuid4()),
                'nome': nome,
                'horario': horario,
                'telefone': telefone,
                'status': 'Pendente',
                'notificado': False
            })
            salvar_agenda(agenda)
    pendentes = [a for a in agenda if a.get('status') != 'Finalizado']
    finalizados = [a for a in agenda if a.get('status') == 'Finalizado']
    notificacoes = verificar_notificacoes()
    return render_template_string("""
<!DOCTYPE html>
<html lang="pt-br">
<head>
    <meta charset="UTF-8">
    <title>Agenda de Agendamentos - Studio de Beleza</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.css" rel="stylesheet">
    <style>
        body { background: #f8fafc; }
        .status-pendente { color: #ffc107; font-weight: bold; }
        .status-finalizado { color: #198754; font-weight: bold; }
        .icon-btn { border: none; background: none; padding: 0; }
        .card { border-radius: 1rem; }
        .table th, .table td { vertical-align: middle; }
        .table-responsive { margin-bottom: 2rem; }
        .btn-sm { font-size: 0.95rem; }
        @media (max-width: 768px) {
            .table-responsive { font-size: 0.95rem; }
            h2 { font-size: 1.1rem; }
            h4 { font-size: 1rem; }
            .card { padding: 0.5rem; }
            .logo { height: 40px !important; }
        }
        @media (max-width: 576px) {
            .container { padding: 0.5rem !important; }
            .card { padding: 0.5rem; }
            .table th, .table td { padding: 0.3rem; }
            .logo { height: 32px !important; }
        }
    </style>
</head>
<body>
<div class="container py-3">
    <div class="text-center mb-4">
        <img src="/static/logo-net30.png" alt="Studio de Beleza" class="logo" style="height:60px;max-width:100%;object-fit:contain;">
        <h1 class="mt-2 mb-0" style="font-size:2rem;font-weight:700;letter-spacing:1px;color:#0d6efd;">Studio de Beleza</h1>
    </div>
    <div class="row justify-content-center">
        <div class="col-lg-10 col-md-12">
            <div class="card shadow-sm">
                <div class="card-body">
                    {% if notificacoes %}
                        <script>playNotificationSound && playNotificationSound();</script>
                        <div class="alert alert-info" role="alert">
                            {% for n in notificacoes %}
                                <div>{{ n }}</div>
                            {% endfor %}
                        </div>
                    {% endif %}
                    <div class="d-flex flex-column flex-md-row justify-content-between align-items-center mb-3 gap-2">
                        <h2 class="text-primary mb-0"><i class="bi bi-calendar2-check"></i> Bem-vindo, {{session['usuario']}}</h2>
                        <a href="/logout" class="btn btn-outline-danger"><i class="bi bi-box-arrow-right"></i> Sair</a>
                    </div>
                    <!-- Remova ou comente este bloco do formulário de novo agendamento -->
{# 
<form method="post" class="row g-3 mb-4 align-items-end">
    <div class="col-md-4">
        <label class="form-label">Nome</label>
        <input name="nome" class="form-control" placeholder="Nome do cliente" required>
    </div>
    <div class="col-md-4">
        <label class="form-label">Data e hora</label>
        <input name="horario" class="form-control" placeholder="dd/mm/yyyy HH:MM" required>
    </div>
    <div class="col-md-3">
        <label class="form-label">WhatsApp</label>
        <input name="telefone" class="form-control" placeholder="+5511999999999" required>
    </div>
    <div class="col-md-1 d-grid">
        <button type="submit" class="btn btn-primary"><i class="bi bi-plus-circle"></i></button>
    </div>
</form>
#}                   
                    <form method="get" class="mb-3">
    <input name="busca" class="form-control" placeholder="Filtrar por profissional ou serviço">
</form>
                    <h4 class="mt-4 mb-3 text-warning"><i class="bi bi-hourglass-split"></i> Pendentes</h4>
                    <div class="table-responsive">
                        <table class="table table-striped table-bordered align-middle">
                            <thead class="table-dark">
                                <tr>
                                    <th>#</th>
                                    <th><i class="bi bi-person"></i> Nome</th>
                                    <th><i class="bi bi-clock"></i> Horário</th>
                                    <th><i class="bi bi-whatsapp"></i> WhatsApp</th>
                                    <th>Status</th>
                                    <th>Serviço</th>
                                    <th>Profissional</th>
                                    <th>Ação</th>
                                </tr>
                            </thead>
                            <tbody>
                                {% for a in pendentes %}
                                <tr>
                                    <td>{{ loop.index }}</td>
                                    <td>{{a.nome}}</td>
                                    <td>{{a.horario}}</td>
                                    <td>
                                        <a href="https://wa.me/{{ a.telefone|replace('+','') }}" target="_blank" class="text-success" title="Abrir WhatsApp">
                                            <i class="bi bi-whatsapp"></i> {{a.telefone}}
                                        </a>
                                    </td>
                                    <td>
                                        <span class="status-pendente"><i class="bi bi-hourglass-split"></i> {{a.status}}</span>
                                    </td>
                                    <td>{{ a.servico if a.servico else '-' }}</td>
                                    <td>{{ a.profissional if a.profissional else '-' }}</td>
                                    <td>
                                        <a href="/status/{{ a.id }}/Finalizado" class="btn btn-success btn-sm" title="Finalizar" aria-label="Finalizar agendamento">
                                            <i class="bi bi-check2-circle"></i> Finalizar
                                        </a>
                                    </td>
                                </tr>
                                {% endfor %}
                            </tbody>
                        </table>
                    </div>
                    <h4 class="mt-5 mb-3 text-success"><i class="bi bi-check2-all"></i> Finalizados</h4>
                    <div class="table-responsive">
                        <table class="table table-striped table-bordered align-middle">
                            <thead class="table-dark">
                                <tr>
                                    <th>#</th>
                                    <th><i class="bi bi-person"></i> Nome</th>
                                    <th><i class="bi bi-clock"></i> Horário</th>
                                    <th><i class="bi bi-whatsapp"></i> WhatsApp</th>
                                    <th>Status</th>
                                    <th>Serviço</th>
                                    <th><i class="bi bi-calendar-check"></i> Finalizado em</th>
                                </tr>
                            </thead>
                            <tbody>
                                {% for a in finalizados %}
                                <tr>
                                    <td>{{ loop.index }}</td>
                                    <td>{{a.nome}}</td>
                                    <td>{{a.horario}}</td>
                                    <td>
                                        <a href="https://wa.me/{{ a.telefone|replace('+','') }}" target="_blank" class="text-success" title="Abrir WhatsApp">
                                            <i class="bi bi-whatsapp"></i> {{a.telefone}}
                                        </a>
                                    </td>
                                    <td>
                                        <span class="status-finalizado"><i class="bi bi-check-circle"></i> {{a.status}}</span>
                                    </td>
                                    <td>{{ a.servico if a.servico else '-' }}</td>
                                    <td>
                                        {{ a.finalizado_em if a.finalizado_em else '-' }}
                                    </td>
                                </tr>
                                {% endfor %}
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>
            <footer class="text-center mt-4 text-muted small">
                <i class="bi bi-code-slash"></i> Desenvolvido com Flask & Bootstrap
            </footer>
        </div>
    </div>
</div>
</body>
</html>
    """, pendentes=pendentes, finalizados=finalizados, notificacoes=notificacoes)

@app.route('/status/<id>/<novo_status>')
def atualizar_status(id, novo_status):
    for ag in agenda:
        if ag.get('id') == id:
            ag['status'] = novo_status
            if novo_status == "Finalizado":
                ag['finalizado_em'] = datetime.datetime.now().strftime("%d/%m/%Y %H:%M")
            salvar_agenda(agenda)
            break
    return redirect(url_for('home'))

@app.route('/agendar', methods=['GET', 'POST'])
def portal_cliente():
    servicos = [
        'Design de Sobrancelhas',
        'Alongamento de Cílios',
        'Manicure',
        'Pedicure',
        'Corte de Cabelo',
        'Escova',
        'Coloração',
        'Hidratação',
        'Penteado',
        'Depilação Facial'
    ]
    horarios_disponiveis = []
    hoje = datetime.datetime.now().strftime("%d/%m/%Y")
    # Gera horários de 09:00 às 17:00 de hora em hora
    for h in range(9, 18):
        horario = f"{hoje} {h:02d}:00"
        if not any(a['horario'] == horario and a['status'] != 'Finalizado' for a in agenda):
            horarios_disponiveis.append(horario)
    mensagem = ""
    if request.method == 'POST':
        nome = request.form.get('nome')
        telefone = request.form.get('telefone')
        servico = request.form.get('servico')
        horario = request.form.get('horario')
        if nome and telefone and servico and horario:
            agenda.append({
                'id': str(uuid.uuid4()),
                'nome': nome,
                'horario': horario,
                'telefone': telefone,
                'servico': servico,
                'status': 'Pendente',
                'notificado': False
            })
            salvar_agenda(agenda)
            mensagem = "Agendamento realizado com sucesso!"
    return render_template_string("""
<!DOCTYPE html>
<html lang="pt-br">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Agendamento Online - Studio de Beleza</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.css" rel="stylesheet">
    <style>
        body { background: #f8fafc; }
        .card { border-radius: 1rem; }
        .form-label { font-weight: 500; }
        .btn-primary, .btn-success { width: 100%; }
        .logo { height: 60px; max-width: 100%; object-fit: contain; }
        @media (max-width: 576px) {
            h2 { font-size: 1.5rem; }
            .container { padding: 0.5rem !important; }
            .logo { height: 40px !important; }
        }
    </style>
</head>
<body>
<div class="container py-4">
    <div class="row justify-content-center">
        <div class="col-lg-7 col-md-9">
            <div class="card shadow-sm p-4">
                <div class="text-center mb-3">
                    <img src="/static/logo-net30.png" alt="Studio de Beleza" class="logo mb-2">
                    <h2 class="mb-0 text-primary" style="font-weight:700;letter-spacing:1px;">Studio de Beleza</h2>
                    <div class="text-muted small">Agendamento de Sobrancelhas, Cílios, Unhas, Cabelos e mais</div>
                </div>
                <h4 class="mb-4 text-center text-primary"><i class="bi bi-calendar2-plus"></i> Agende seu horário</h4>
                {% if mensagem %}
                    <div class="alert alert-success text-center">{{ mensagem }}</div>
                {% endif %}
                <form method="post" class="row g-3">
                    <div class="col-12 col-md-6">
                        <label class="form-label">Nome</label>
                        <input name="nome" class="form-control" required>
                    </div>
                    <div class="col-12 col-md-6">
                        <label class="form-label">Telefone</label>
                        <input name="telefone" class="form-control" required>
                    </div>
                    <div class="col-12">
                        <label class="form-label">Serviço</label>
                        <select name="servico" class="form-select" required>
                            <option value="">Selecione...</option>
                            {% for s in servicos %}
                                <option value="{{s}}">{{s}}</option>
                            {% endfor %}
                        </select>
                    </div>
                    <div class="col-12">
                        <label class="form-label">Horário disponível</label>
                        <select name="horario" class="form-select" required>
                            <option value="">Selecione...</option>
                            {% for h in horarios_disponiveis %}
                                <option value="{{h}}">{{h}}</option>
                            {% endfor %}
                        </select>
                    </div>
                    <div class="col-12">
                        <button type="submit" class="btn btn-primary mt-2">Confirmar Agendamento</button>
                    </div>
                </form>
                {% if mensagem and telefone %}
                    <a class="btn btn-success mt-3"
                    href="https://wa.me/{{ telefone|replace('+','') }}?text={{ ('Olá, seu agendamento para o serviço de ' ~ servico ~ ' está confirmado para ' ~ horario ~ '.')|urlencode }}"
                    target="_blank">
                        Confirmar pelo WhatsApp
                    </a>
                {% endif %}
            </div>
        </div>
    </div>
</div>
</body>
</html>
""",
servicos=servicos,
horarios_disponiveis=horarios_disponiveis,
mensagem=mensagem,
telefone=telefone if request.method == 'POST' else '',
servico=servico if request.method == 'POST' else '',
horario=horario if request.method == 'POST' else ''
)
# Remova ou comente o bloco abaixo em hospedagem!
if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True, port=5000)

# Inicializar com dados de exemplo (remover em produção)
if not agenda:
    agenda = [
        {
            "id": str(uuid.uuid4()),
            "nome": "João",
            "horario": "08/06/2025 10:00",
            "telefone": "+5511999999999",
            "status": "Pendente",
            "notificado": False
        }
    ]
    salvar_agenda(agenda)

profissionais = [
    {"nome": "Ana", "especialidades": ["Design de Sobrancelhas", "Manicure"], "disponivel": True},
    {"nome": "Bruna", "especialidades": ["Cílios", "Cabelos", "Escova"], "disponivel": True},
    {"nome": "Carla", "especialidades": ["Unhas", "Pedicure"], "disponivel": True},
    # Adicione mais profissionais conforme necessário
]

def sugerir_profissional(servico):
    # Retorna o primeiro profissional disponível com a especialidade
    for p in profissionais:
        if servico in p["especialidades"] and p["disponivel"]:
            return p["nome"]
    return "A definir"

