from flask import Flask, render_template, redirect, url_for, flash, request
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from datetime import datetime, timezone # Importação correta
from sqlalchemy.exc import IntegrityError

# Importações dos seus módulos locais
from models import db, Ata, Contrato, Contratinho, Empenho, ItemAta, UnidadeSaude
from forms import AtaForm, ContratoForm, ContratinhoForm, EmpenhoForm, ItemAtaForm, UnidadeSaudeForm
import reports 

app = Flask(__name__)

# Configurações da Aplicação
app.config['SECRET_KEY'] = 'mude-esta-chave-para-algo-super-secreto-e-unico-agora!' 
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///saude_contratos.db' # Será sobrescrito pela DATABASE_URL no Render
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['LIMITE_SALDO_BAIXO'] = 10 

# Lógica para usar DATABASE_URL do Render (PostgreSQL) ou SQLite localmente
DATABASE_URL_RENDER = os.environ.get('DATABASE_URL')
if DATABASE_URL_RENDER:
    uri = DATABASE_URL_RENDER
    if uri.startswith("postgres://"):
        uri = uri.replace("postgres://", "postgresql://", 1)
    # Remove ?sslmode=require (ou similar) se presente, para conexões internas no Render
    if '?sslmode=' in uri:
        uri = uri.split('?sslmode=')[0]
    app.config['SQLALCHEMY_DATABASE_URI'] = uri
else:
    # Configuração local com SQLite (para desenvolvimento)
    basedir = os.path.abspath(os.path.dirname(__file__))
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'saude_contratos.db')


@app.context_processor
def inject_current_year():
    return {'ano_atual': datetime.now(timezone.utc).year} # CORRIGIDO AQUI

db.init_app(app)
migrate = Migrate(app, db)

# --- ROTA PARA O DASHBOARD ---
@app.route('/dashboard')
def dashboard():
    totais = {
        'atas': Ata.query.count(),
        'contratos': Contrato.query.count(),
        'contratinhos': Contratinho.query.count(),
        'empenhos': Empenho.query.count(),
        'itens_ata': ItemAta.query.count(),
        'unidades_saude': UnidadeSaude.query.count()
    }
    limite = app.config['LIMITE_SALDO_BAIXO']
    itens_saldo_baixo = ItemAta.query.filter(
        ItemAta.saldo_disponivel <= limite,
        ItemAta.quantidade_registrada > 0 
    ).order_by(ItemAta.saldo_disponivel).all()

    return render_template('dashboard.html',
                           titulo_pagina="Dashboard",
                           totais=totais,
                           itens_saldo_baixo=itens_saldo_baixo,
                           limite_saldo_baixo=limite)

# --- ROTAS PARA ATAS ---
@app.route('/') 
@app.route('/atas') 
def index(): 
    todas_as_atas = Ata.query.order_by(Ata.ano.desc(), Ata.numero_ata.desc()).all()
    return render_template('listar_atas.html', 
                           titulo_pagina="Atas Registradas",
                           lista_de_atas=todas_as_atas)

@app.route('/ata/nova', methods=['GET', 'POST'])
def criar_ata():
    form = AtaForm()
    if form.validate_on_submit():
        try:
            nova_ata_db = Ata(numero_ata=form.numero_ata.data, ano=form.ano.data,
                              descricao=form.descricao.data, data_assinatura=form.data_assinatura.data,
                              data_validade=form.data_validade.data)
            db.session.add(nova_ata_db)
            db.session.commit()
            flash('Ata criada com sucesso! Agora adicione os itens a esta ata.', 'success')
            return redirect(url_for('listar_itens_da_ata', ata_id=nova_ata_db.id))
        except IntegrityError:
            db.session.rollback()
            flash('Erro: Já existe uma ata com este número. Verifique os dados.', 'danger')
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao criar ata: {str(e)}', 'danger')
    return render_template('criar_ata.html', titulo_pagina="Criar Nova Ata", form=form)

@app.route('/ata/editar/<int:ata_id>', methods=['GET', 'POST'])
def editar_ata(ata_id):
    ata_para_editar = Ata.query.get_or_404(ata_id)
    form = AtaForm(obj=ata_para_editar)
    if form.validate_on_submit():
        try:
            form.populate_obj(ata_para_editar)
            db.session.commit()
            flash('Ata atualizada com sucesso!', 'success')
            return redirect(url_for('index'))
        except IntegrityError:
            db.session.rollback()
            flash('Erro: Já existe uma ata com este número. Verifique os dados.', 'danger')
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao atualizar ata: {str(e)}', 'danger')
    return render_template('editar_ata.html', titulo_pagina="Editar Ata", form=form, ata_id=ata_id)

@app.route('/ata/excluir/<int:ata_id>', methods=['GET'])
def excluir_ata(ata_id):
    ata_para_excluir = Ata.query.get_or_404(ata_id)
    try:
        db.session.delete(ata_para_excluir)
        db.session.commit()
        flash('Ata e todos os seus itens, contratos, contratinhos e empenhos vinculados foram excluídos com sucesso!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao excluir ata: {str(e)}', 'danger')
    return redirect(url_for('index'))

# --- ROTAS PARA ITENS DA ATA ---
@app.route('/ata/<int:ata_id>/itens')
def listar_itens_da_ata(ata_id):
    ata = Ata.query.get_or_404(ata_id)
    tipo_item_display_map = dict(ItemAta.TIPO_ITEM_CHOICES)
    itens = ItemAta.query.filter_by(ata_id=ata.id).order_by(ItemAta.descricao_item).all()
    return render_template('listar_itens_ata.html',
                           titulo_pagina=f"Itens da Ata {ata.numero_ata}",
                           ata=ata,
                           itens_da_ata=itens,
                           tipo_item_display_map=tipo_item_display_map)

@app.route('/ata/<int:ata_id>/item/novo', methods=['GET', 'POST'])
def criar_item_ata(ata_id):
    ata = Ata.query.get_or_404(ata_id)
    form = ItemAtaForm()
    if form.validate_on_submit():
        try:
            novo_item = ItemAta()
            form.populate_obj(novo_item) 
            novo_item.ata_id = ata.id 
            novo_item.saldo_disponivel = novo_item.quantidade_registrada 
            
            db.session.add(novo_item)
            db.session.commit()
            flash('Item adicionado à ata com sucesso!', 'success')
            return redirect(url_for('listar_itens_da_ata', ata_id=ata.id))
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao adicionar item à ata: {str(e)}', 'danger')
    return render_template('criar_item_ata.html',
                           titulo_pagina="Adicionar Item à Ata",
                           form=form,
                           ata_id_ref=ata.id, 
                           ata_numero=ata.numero_ata)

@app.route('/ata/<int:ata_id>/item/<int:item_id>/editar', methods=['GET', 'POST'])
def editar_item_ata(ata_id, item_id):
    ata = Ata.query.get_or_404(ata_id)
    item_para_editar = ItemAta.query.get_or_404(item_id)
    if item_para_editar.ata_id != ata.id: 
        flash('Item não pertence à ata especificada.', 'danger')
        return redirect(url_for('listar_itens_da_ata', ata_id=ata.id))

    saldo_antes_edicao = item_para_editar.saldo_disponivel
    qtd_registrada_antes_edicao = item_para_editar.quantidade_registrada
    form = ItemAtaForm(obj=item_para_editar)

    if form.validate_on_submit():
        try:
            qtd_consumida_total = qtd_registrada_antes_edicao - saldo_antes_edicao
            
            form.populate_obj(item_para_editar)
            
            novo_saldo = item_para_editar.quantidade_registrada - qtd_consumida_total
            if novo_saldo < 0:
                flash('A nova quantidade registrada é menor que a quantidade já consumida. Ajuste os consumos ou aumente a quantidade.', 'danger')
                form.quantidade_registrada.data = qtd_registrada_antes_edicao
            else:
                item_para_editar.saldo_disponivel = novo_saldo
                db.session.commit()
                flash('Item da ata atualizado com sucesso!', 'success')
                return redirect(url_for('listar_itens_da_ata', ata_id=ata.id))
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao atualizar item da ata: {str(e)}', 'danger')
            
    return render_template('editar_item_ata.html',
                           titulo_pagina="Editar Item da Ata",
                           form=form,
                           ata_id_ref=ata.id,
                           ata_numero=ata.numero_ata,
                           item_id=item_id,
                           saldo_atual_item=item_para_editar.saldo_disponivel)

@app.route('/ata/<int:ata_id>/item/<int:item_id>/excluir', methods=['GET'])
def excluir_item_ata(ata_id, item_id):
    ata = Ata.query.get_or_404(ata_id) 
    item_para_excluir = ItemAta.query.get_or_404(item_id)
    if item_para_excluir.ata_id != ata.id:
        flash('Item não pertence à ata especificada.', 'danger')
        return redirect(url_for('listar_itens_da_ata', ata_id=ata.id))

    if item_para_excluir.quantidade_registrada != item_para_excluir.saldo_disponivel:
        flash('Este item não pode ser excluído pois já possui consumos. Remova os consumos primeiro ou ajuste os saldos.', 'danger')
        return redirect(url_for('listar_itens_da_ata', ata_id=ata.id))
        
    try:
        db.session.delete(item_para_excluir)
        db.session.commit()
        flash('Item da ata excluído com sucesso!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao excluir item da ata: {str(e)}', 'danger')
    return redirect(url_for('listar_itens_da_ata', ata_id=ata.id))

# --- ROTAS PARA CONTRATOS ---
@app.route('/contratos')
def listar_contratos():
    todos_os_contratos = Contrato.query.order_by(Contrato.numero_contrato.desc()).all()
    return render_template('listar_contratos.html',
                           titulo_pagina="Lista de Contratos",
                           lista_de_contratos=todos_os_contratos)

@app.route('/contrato/novo', methods=['GET', 'POST'])
def criar_contrato():
    form = ContratoForm()
    if form.validate_on_submit():
        try:
            novo_contrato_db = Contrato() 
            form.populate_obj(novo_contrato_db) 
            db.session.add(novo_contrato_db)
            db.session.commit()
            flash('Contrato criado com sucesso!', 'success')
            return redirect(url_for('listar_contratos'))
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao criar contrato: {str(e)}', 'danger')
    return render_template('criar_contrato.html', titulo_pagina="Criar Novo Contrato", form=form)

@app.route('/contrato/editar/<int:contrato_id>', methods=['GET', 'POST'])
def editar_contrato(contrato_id):
    contrato_para_editar = Contrato.query.get_or_404(contrato_id)
    form = ContratoForm(obj=contrato_para_editar)
    if form.validate_on_submit():
        try:
            form.populate_obj(contrato_para_editar)
            db.session.commit()
            flash('Contrato atualizado com sucesso!', 'success')
            return redirect(url_for('listar_contratos'))
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao atualizar contrato: {str(e)}', 'danger')
    return render_template('editar_contrato.html', titulo_pagina="Editar Contrato", form=form, contrato_id=contrato_id)

@app.route('/contrato/excluir/<int:contrato_id>', methods=['GET'])
def excluir_contrato(contrato_id):
    contrato_para_excluir = Contrato.query.get_or_404(contrato_id)
    try:
        db.session.delete(contrato_para_excluir)
        db.session.commit()
        flash('Contrato excluído com sucesso!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao excluir contrato: {str(e)}', 'danger')
    return redirect(url_for('listar_contratos'))

# --- ROTAS PARA UNIDADES DE SAÚDE ---
@app.route('/unidades')
def listar_unidades():
    unidades = UnidadeSaude.query.order_by(UnidadeSaude.nome_unidade).all()
    unidade_tipo_map = dict(UnidadeSaude.TIPO_UNIDADE_CHOICES)
    return render_template('listar_unidades.html', 
                           titulo_pagina="Unidades de Saúde", 
                           unidades=unidades,
                           unidade_tipo_map=unidade_tipo_map)

@app.route('/unidade/nova', methods=['GET', 'POST'])
def criar_unidade():
    form = UnidadeSaudeForm()
    if form.validate_on_submit():
        try:
            nova_unidade = UnidadeSaude()
            form.populate_obj(nova_unidade)
            db.session.add(nova_unidade)
            db.session.commit()
            flash('Unidade de Saúde cadastrada com sucesso!', 'success')
            return redirect(url_for('listar_unidades'))
        except IntegrityError:
            db.session.rollback()
            flash('Erro: Já existe uma Unidade de Saúde com este nome.', 'danger')
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao cadastrar unidade: {str(e)}', 'danger')
    return render_template('criar_unidade.html', titulo_pagina="Cadastrar Unidade de Saúde", form=form)

@app.route('/unidade/editar/<int:unidade_id>', methods=['GET', 'POST'])
def editar_unidade(unidade_id):
    unidade_para_editar = UnidadeSaude.query.get_or_404(unidade_id)
    form = UnidadeSaudeForm(obj=unidade_para_editar)
    if form.validate_on_submit():
        try:
            form.populate_obj(unidade_para_editar)
            db.session.commit()
            flash('Unidade de Saúde atualizada com sucesso!', 'success')
            return redirect(url_for('listar_unidades'))
        except IntegrityError:
            db.session.rollback()
            flash('Erro: Já existe uma Unidade de Saúde com este nome (se estiver alterando).', 'danger')
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao atualizar unidade: {str(e)}', 'danger')
    return render_template('editar_unidade.html', titulo_pagina="Editar Unidade de Saúde", form=form, unidade_id=unidade_id)

@app.route('/unidade/excluir/<int:unidade_id>', methods=['GET'])
def excluir_unidade(unidade_id):
    unidade_para_excluir = UnidadeSaude.query.get_or_404(unidade_id)
    if unidade_para_excluir.contratinhos_vinculados.first() or unidade_para_excluir.empenhos_vinculados.first():
        flash('Esta Unidade de Saúde não pode ser excluída pois está vinculada a Contratinhos ou Empenhos.', 'danger')
        return redirect(url_for('listar_unidades'))
    try:
        db.session.delete(unidade_para_excluir)
        db.session.commit()
        flash('Unidade de Saúde excluída com sucesso!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao excluir unidade: {str(e)}', 'danger')
    return redirect(url_for('listar_unidades'))

# --- ROTAS PARA CONTRATINHOS ---
@app.route('/contratinhos')
def listar_contratinhos():
    todos_os_contratinhos = Contratinho.query.order_by(Contratinho.data_emissao.desc()).all()
    return render_template('listar_contratinhos.html',
                           titulo_pagina="Lista de Contratinhos",
                           lista_de_contratinhos=todos_os_contratinhos)

@app.route('/contratinho/novo', methods=['GET', 'POST'])
def criar_contratinho():
    form = ContratinhoForm() 
    if form.validate_on_submit():
        item_id = form.item_ata_id.data 
        quantidade_a_consumir = form.quantidade_consumida.data if form.quantidade_consumida.data else 0
        item_afetado = None

        if item_id and quantidade_a_consumir > 0:
            item_afetado = ItemAta.query.get(item_id)
            if not item_afetado:
                flash('Item da ata selecionado para consumo não encontrado.', 'danger')
                return render_template('criar_contratinho.html', titulo_pagina="Registrar Contratinho", form=form)
            if item_afetado.ata_id != form.ata_id.data:
                flash('O item selecionado não pertence à ata selecionada para o contratinho.', 'danger')
                return render_template('criar_contratinho.html', titulo_pagina="Registrar Contratinho", form=form)
            if item_afetado.saldo_disponivel < quantidade_a_consumir:
                flash(f'Saldo insuficiente para o item "{item_afetado.descricao_item}". Saldo disponível: {item_afetado.saldo_disponivel}', 'danger')
                return render_template('criar_contratinho.html', titulo_pagina="Registrar Contratinho", form=form)
        elif item_id and quantidade_a_consumir <= 0:
            flash('Se um item for selecionado para consumo, a quantidade consumida deve ser maior que zero.', 'danger')
            return render_template('criar_contratinho.html', titulo_pagina="Registrar Contratinho", form=form)
        elif not item_id and quantidade_a_consumir > 0: 
            form.item_ata_id.data = None 
            form.quantidade_consumida.data = 0 
            flash('Se uma quantidade for consumida, um item da ata deve ser selecionado. Nenhum item/quantidade será consumido desta vez.', 'warning')
            
        try:
            novo_contratinho = Contratinho()
            form.populate_obj(novo_contratinho) 
            if not novo_contratinho.item_ata_id:
                novo_contratinho.quantidade_consumida = 0

            db.session.add(novo_contratinho)
            
            if item_afetado and novo_contratinho.item_ata_id and quantidade_a_consumir > 0 : 
                item_afetado.saldo_disponivel -= quantidade_a_consumir
            db.session.commit()
            flash('Contratinho registrado com sucesso!', 'success')
            if item_afetado and novo_contratinho.item_ata_id and quantidade_a_consumir > 0:
                 flash(f'Saldo do item "{item_afetado.descricao_item}" atualizado.', 'info')
            return redirect(url_for('listar_contratinhos'))
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao registrar contratinho: {str(e)}', 'danger')
    return render_template('criar_contratinho.html', titulo_pagina="Registrar Contratinho", form=form)

@app.route('/contratinho/editar/<int:contratinho_id>', methods=['GET', 'POST'])
def editar_contratinho(contratinho_id):
    ct_para_editar = Contratinho.query.get_or_404(contratinho_id)
    ata_atual_do_ct = Ata.query.get(ct_para