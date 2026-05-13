from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone

# Create your models here.
class Eleitor(models.Model):
    nome = models.CharField(max_length=150)
    email = models.EmailField(unique=True)
    cpf = models.CharField(max_length=14, unique=True)
    data_nascimento = models.DateField()
    ativo = models.BooleanField(default=True)
    data_cadastro = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.nome

class Eleicao(models.Model):
    titulo = models.CharField(max_length=200)
    descricao = models.TextField(blank=True)
    tipo = models.CharField(max_length=20, choices=[
        ('estudantil', 'Estudantil'),
        ('sindical', 'Sindical'),
        ('associacao', 'Associacão'),
        ('condominio', 'Condomínio'),
        ('conselho', 'Conselho'),
        ('outra', 'Outra')
    ])
    data_inicio = models.DateTimeField()
    data_fim = models.DateTimeField()
    status = models.CharField(max_length=20, choices=[
        ('rascunho', 'Rascunho'),
        ('aberta', 'Aberta'),
        ('encerrada', 'Encerrada'),
        ('apurada', 'Apurada')
    ], default='rascunho')
    permite_branco = models.BooleanField(default=True)
    criada_por = models.ForeignKey(Eleitor, on_delete=models.PROTECT, related_name='eleicoes_criadas')

    def clean(self):
        if self.data_fim <= self.data_inicio:
            raise ValidationError('A data de fim tem que ser depois da data de início.')
        
        if self.pk:
            antigo_status = Eleicao.objects.get(pk=self.pk).status
            if antigo_status != self.status:
                fluxo = {
                    'rascunho': ['aberta'],
                    'aberta': ['encerrada'],
                    'encerrada': ['apurada'],
                    'apurada': []
                }
                if self.status not in fluxo.get(antigo_status, []):
                    raise ValidationError(f'Transicão de status inválida: {antigo_status} para {self.status}')

    def __str__(self):
        return self.titulo

class Candidato(models.Model):
    eleicao = models.ForeignKey(Eleicao, on_delete=models.CASCADE, related_name='candidatos')
    numero = models.PositiveIntegerField() 
    nome = models.CharField(max_length=150)
    nome_urna = models.CharField(max_length=50)
    partido_ou_chapa = models.CharField(max_length=100, blank=True)
    proposta = models.TextField(blank=True)
    foto_url = models.URLField(blank=True)

    class Meta:
        unique_together = ('eleicao', 'numero')

    def __str__(self):
        return f"{self.numero} - {self.nome}"

class AptidaoEleitor(models.Model):
    eleitor = models.ForeignKey(Eleitor, on_delete=models.PROTECT, related_name='aptidoes')
    eleicao = models.ForeignKey(Eleicao, on_delete=models.CASCADE, related_name='aptos')
    data_inclusao = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('eleitor', 'eleicao')

    def __str__(self):
        return f"{self.eleitor} - {self.eleicao}"

class RegistroVotacao(models.Model):
    eleitor = models.ForeignKey(Eleitor, on_delete=models.PROTECT, related_name='registros_votacao')
    eleicao = models.ForeignKey(Eleicao, on_delete=models.PROTECT, related_name='registros_votacao')
    data_hora = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('eleitor', 'eleicao')

    def __str__(self):
        return f"{self.eleitor} - {self.eleicao}"

class Voto(models.Model):
    eleicao = models.ForeignKey(Eleicao, on_delete=models.PROTECT, related_name='votos')
    candidato = models.ForeignKey(Candidato, on_delete=models.PROTECT, related_name='votos', null=True, blank=True)
    em_branco = models.BooleanField(default=False)
    data_hora = models.DateTimeField(auto_now_add=True)
    comprovante_hash = models.CharField(max_length=64, unique=True) 

    def clean(self):
        if self.em_branco and self.candidato is not None:
            raise ValidationError(' voto em branco não possui um candidato associado.')
        if not self.em_branco and self.candidato is None:
            raise ValidationError(' voto válido deve ter possuir um candidato associado.')

    def __str__(self):
        return f"Voto para {self.candidato} na eleicão {self.eleicao}"
