from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, IntegerField, DateField, SubmitField, FloatField, SelectField, BooleanField
from wtforms.validators import DataRequired, Length, Optional, NumberRange, ValidationError, Email
from models import Ata, ItemAta, UnidadeSaude # Adicionado UnidadeSaude

# Função Coerce customizada para SelectFields opcionais que devem ser inteiros ou None
def coerce_int_or_none(x):
    if x is None or str(x).strip() == '': # Se for None ou string vazia
        return None # Retorna None (para campos opcionais)
    try:
        return int(x) # Tenta converter para inteiro
    except ValueError:
        raise ValidationError('Valor inválido para seleção de item.')


# Lista de formatos de data que vamos aceitar
DATE_FORMATS = ['%Y-%m-%d', '%d/%m/%Y']

class AtaForm(FlaskForm):
    numero_ata = StringField('Número da Ata', 
                             validators=[DataRequired(message="Este campo é obrigatório."), 
                                         Length(min=3, max=100, message="Deve ter entre 3 e 100 caracteres.")])
    ano = IntegerField('Ano da Ata', 
                       validators=[DataRequired(message="Este campo é obrigatório.")])
    descricao = TextAreaField('Descrição', 
                              validators=[Optional(), Length(max=500)])
    data_assinatura = DateField('Data de Assinatura (DD/MM/AAAA ou AAAA-MM-DD)', 
                                format=DATE_FORMATS, 
                                validators=[Optional()])
    data_validade = DateField('Data de Validade (DD/MM/AAAA ou AAAA-MM-DD)', 
                              format=DATE_FORMATS, 
                              validators=[Optional()])
    submit = SubmitField('Salvar Ata')

class ItemAtaForm(FlaskForm):
    descricao_item = StringField('Descrição do Item', 
                                 validators=[DataRequired(message="Campo obrigatório."), Length(max=255)])
    tipo_item = SelectField('Tipo do Item', 
                            choices=ItemAta.TIPO_ITEM_CHOICES, 
                            validators=[DataRequired(message="Selecione o tipo do item.")])
    unidade_medida = StringField('Unidade de Medida (Ex: Und, Cx, Kg)', 
                                 validators=[Optional(), Length(max=50)])
    quantidade_registrada = FloatField('Quantidade Registrada na Ata', 
                                       validators=[DataRequired(message="Campo obrigatório."), NumberRange(min=0)])
    valor_unitario_registrado = FloatField('Valor Unitário (R$)', 
                                           validators=[Optional(), NumberRange(min=0)])
    principio_ativo = StringField('Princípio Ativo (Medicamentos)', 
                                  validators=[Optional(), Length(max=255)])
    lote = StringField('Lote (Medicamentos)', 
                       validators=[Optional(), Length(max=100)])
    data_garantia_fim = DateField('Data Fim da Garantia (DD/MM/AAAA ou AAAA-MM-DD)', 
                                  format=DATE_FORMATS, 
                                  validators=[Optional()])
    requer_calibracao = BooleanField('Requer Calibração Periódica?')
    ultima_calibracao = DateField('Data da Última Calibração (DD/MM/AAAA ou AAAA-MM-DD)', 
                                  format=DATE_FORMATS, 
                                  validators=[Optional()])
    proxima_calibracao = DateField('Data da Próxima Calibração (DD/MM/AAAA ou AAAA-MM-DD)', 
                                   format=DATE_FORMATS, 
                                   validators=[Optional()])
    reutilizavel = BooleanField('Item é Reutilizável?')
    submit = SubmitField('Salvar Item da Ata')

class UnidadeSaudeForm(FlaskForm):
    nome_unidade = StringField('Nome da Unidade', 
                               validators=[DataRequired(message="Nome é obrigatório."), Length(max=150)])
    tipo_unidade = SelectField('Tipo da Unidade', 
                               choices=UnidadeSaude.TIPO_UNIDADE_CHOICES, 
                               validators=[DataRequired(message="Selecione um tipo válido.")])
    endereco = StringField('Endereço', 
                           validators=[Optional(), Length(max=255)])
    telefone = StringField('Telefone', 
                           validators=[Optional(), Length(max=20)])
    email_responsavel = StringField('Email do Responsável/Contato', 
                                    validators=[Optional(), Email(message="Email inválido."), Length(max=120)])
    submit = SubmitField('Salvar Unidade de Saúde')

    def validate_tipo_unidade(self, field): 
        if field.data == '': 
            raise ValidationError('Selecione um tipo de unidade válido.')

class ContratoForm(FlaskForm):
    numero_contrato = StringField('Número do Contrato', 
                                  validators=[DataRequired(message="Campo obrigatório."), Length(min=3, max=100)])
    objeto = TextAreaField('Objeto do Contrato', 
                           validators=[DataRequired(message="Campo obrigatório."), Length(max=1000)])
    valor_total = FloatField('Valor Total (R$)', 
                             validators=[DataRequired(message="Campo obrigatório."), NumberRange(min=0.01, message="Valor deve ser positivo.")])
    fornecedor = StringField('Fornecedor', 
                             validators=[Optional(), Length(max=200)])
    data_assinatura_contrato = DateField('Data de Assinatura (DD/MM/AAAA ou AAAA-MM-DD)', 
                                         format=DATE_FORMATS, 
                                         validators=[Optional()])
    data_inicio_vigencia = DateField('Início da Vigência (DD/MM/AAAA ou AAAA-MM-DD)', 
                                     format=DATE_FORMATS, 
                                     validators=[Optional()])
    data_fim_vigencia = DateField('Fim da Vigência (DD/MM/AAAA ou AAAA-MM-DD)', 
                                  format=DATE_FORMATS, 
                                  validators=[Optional()])
    ata_id = SelectField('Ata Vinculada (Obrigatório)', 
                         coerce=int, 
                         validators=[DataRequired(message="Selecione uma Ata.")])
    submit = SubmitField('Salvar Contrato')

    def __init__(self, *args, **kwargs):
        super(ContratoForm, self).__init__(*args, **kwargs)
        self.ata_id.choices = [(ata.id, ata.numero_ata) for ata in Ata.query.order_by(Ata.numero_ata).all()]
        if not self.ata_id.choices:
            self.ata_id.choices = []

class ContratinhoForm(FlaskForm):
    numero_contratinho = StringField('Número do Contratinho/Doc.', 
                                     validators=[DataRequired(message="Campo obrigatório."), Length(max=100)])
    objeto = TextAreaField('Objeto do Contratinho (Geral)', 
                           validators=[DataRequired(message="Campo obrigatório."), Length(max=1000)])
    valor = FloatField('Valor Total do Contratinho (R$)', 
                       validators=[DataRequired(message="Campo obrigatório."), NumberRange(min=0.01)])
    favorecido = StringField('Favorecido/Fornecedor', 
                             validators=[Optional(), Length(max=200)])
    data_emissao = DateField('Data de Emissão (DD/MM/AAAA ou AAAA-MM-DD)', 
                             format=DATE_FORMATS, 
                             validators=[DataRequired(message="Campo obrigatório.")])
    ata_id = SelectField('Ata Vinculada (Obrigatório)', 
                         coerce=int, 
                         validators=[DataRequired(message="Selecione uma Ata.")])
    unidade_saude_id = SelectField('Unidade de Saúde Destino (Opcional)', 
                                   coerce=coerce_int_or_none, 
                                   validators=[Optional()])
    item_ata_id = SelectField('Item da Ata Consumido (Opcional)', 
                              coerce=coerce_int_or_none, 
                              validators=[Optional()])
    quantidade_consumida = FloatField('Qtd. Consumida do Item', 
                                      validators=[Optional(), NumberRange(min=0)])
    submit = SubmitField('Salvar Contratinho')

    def __init__(self, ata_obj_para_filtro_de_itens=None, *args, **kwargs):
        super(ContratinhoForm, self).__init__(*args, **kwargs)
        self.ata_id.choices = [(ata.id, ata.numero_ata) for ata in Ata.query.order_by(Ata.numero_ata).all()]
        if not self.ata_id.choices:
            self.ata_id.choices = []

        self.unidade_saude_id.choices = [('', '--- Nenhuma Unidade ---')] + \
                                        [(u.id, u.nome_unidade) for u in UnidadeSaude.query.order_by(UnidadeSaude.nome_unidade).all()]
        
        id_da_ata_selecionada = None
        if self.ata_id.data is not None: 
            id_da_ata_selecionada = self.ata_id.data
        elif ata_obj_para_filtro_de_itens: 
            id_da_ata_selecionada = ata_obj_para_filtro_de_itens.id

        item_choices = []
        if id_da_ata_selecionada:
            item_choices = [(item.id, f"{item.descricao_item} (Saldo: {item.saldo_disponivel})")
                            for item in ItemAta.query.filter_by(ata_id=id_da_ata_selecionada).order_by(ItemAta.descricao_item).all()]
        self.item_ata_id.choices = [('', '--- Nenhum / Não Consumir ---')] + item_choices

class EmpenhoForm(FlaskForm):
    numero_empenho = StringField('Número do Empenho', 
                                 validators=[DataRequired(message="Campo obrigatório."), Length(max=100)])
    descricao_simples = TextAreaField('Descrição Simplificada', 
                                     validators=[DataRequired(message="Campo obrigatório."), Length(max=1000)])
    valor_empenhado = FloatField('Valor Empenhado (R$)', 
                                 validators=[DataRequired(message="Campo obrigatório."), NumberRange(min=0.01)])
    favorecido = StringField('Favorecido', 
                             validators=[Optional(), Length(max=200)])
    data_emissao = DateField('Data de Emissão (DD/MM/AAAA ou AAAA-MM-DD)', 
                             format=DATE_FORMATS, 
                             validators=[DataRequired(message="Campo obrigatório.")])
    ata_id = SelectField('Ata Vinculada (Obrigatório)', 
                         coerce=int, 
                         validators=[DataRequired(message="Selecione uma Ata.")])
    unidade_saude_id = SelectField('Unidade de Saúde Destino (Opcional)', 
                                   coerce=coerce_int_or_none, 
                                   validators=[Optional()])
    item_ata_id = SelectField('Item da Ata Consumido (Opcional)', 
                              coerce=coerce_int_or_none, 
                              validators=[Optional()])
    quantidade_consumida = FloatField('Qtd. Consumida do Item', 
                                      validators=[Optional(), NumberRange(min=0)])
    submit = SubmitField('Salvar Empenho')

    def __init__(self, ata_obj_para_filtro_de_itens=None, *args, **kwargs):
        super(EmpenhoForm, self).__init__(*args, **kwargs)
        self.ata_id.choices = [(ata.id, ata.numero_ata) for ata in Ata.query.order_by(Ata.numero_ata).all()]
        if not self.ata_id.choices:
            self.ata_id.choices = []

        self.unidade_saude_id.choices = [('', '--- Nenhuma Unidade ---')] + \
                                        [(u.id, u.nome_unidade) for u in UnidadeSaude.query.order_by(UnidadeSaude.nome_unidade).all()]

        id_da_ata_selecionada = None
        if self.ata_id.data is not None:
            id_da_ata_selecionada = self.ata_id.data
        elif ata_obj_para_filtro_de_itens:
            id_da_ata_selecionada = ata_obj_para_filtro_de_itens.id
            
        item_choices = []
        if id_da_ata_selecionada:
            item_choices = [(item.id, f"{item.descricao_item} (Saldo: {item.saldo_disponivel})")
                            for item in ItemAta.query.filter_by(ata_id=id_da_ata_selecionada).order_by(ItemAta.descricao_item).all()]
        self.item_ata_id.choices = [('', '--- Nenhum / Não Consumir ---')] + item_choices