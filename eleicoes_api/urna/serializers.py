import re
from rest_framework import serializers
from django.utils import timezone
from .models import Eleitor, Eleicao, Candidato, AptidaoEleitor, RegistroVotacao, Voto

class EleitorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Eleitor
        fields = '__all__'

    def validate_cpf(self, value):
        if not re.match(r'^\d{3}\.\d{3}\.\d{3}-\d{2}$', value):
            raise serializers.ValidationError("Formato invalido de cpf.")
        return value

class EleicaoSerializer(serializers.ModelSerializer):
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    total_candidatos = serializers.SerializerMethodField()
    total_aptos = serializers.SerializerMethodField()

    class Meta:
        model = Eleicao
        fields = '__all__'

    def get_total_candidatos(self, obj):
        return obj.candidatos.count()

    def get_total_aptos(self, obj):
        return obj.aptos.count()

class CandidatoSerializer(serializers.ModelSerializer):
    eleicao_titulo = serializers.ReadOnlyField(source='eleicao.titulo')

    class Meta:
        model = Candidato
        fields = '__all__'

    def validate_numero(self, value):
        if value == 0:
            raise serializers.ValidationError("O número 0 é reservado para votos em branco.")
        return value

class AptidaoEleitorSerializer(serializers.ModelSerializer):
    eleitor_nome = serializers.ReadOnlyField(source='eleitor.nome')
    eleicao_titulo = serializers.ReadOnlyField(source='eleicao.titulo')

    class Meta:
        model = AptidaoEleitor
        fields = '__all__'

class RegistroVotacaoSerializer(serializers.ModelSerializer):
    eleitor_nome = serializers.ReadOnlyField(source='eleitor.nome')
    eleicao_titulo = serializers.ReadOnlyField(source='eleicao.titulo')

    class Meta:
        model = RegistroVotacao
        fields = '__all__'
        read_only_fields = ['eleitor', 'eleicao', 'data_hora']

class VotoSerializer(serializers.ModelSerializer):
    candidato_nome_urna = serializers.ReadOnlyField(source='candidato.nome_urna', allow_null=True)
    em_branco_display = serializers.SerializerMethodField()

    class Meta:
        model = Voto
        fields = ['id', 'eleicao', 'candidato', 'em_branco', 'data_hora', 
                  'candidato_nome_urna', 'em_branco_display']

    def get_em_branco_display(self, obj):
        return "BRANCO" if obj.em_branco else None

class VotacaoInputSerializer(serializers.Serializer):
    eleitor_id = serializers.IntegerField()
    eleicao_id = serializers.IntegerField()
    candidato_id = serializers.IntegerField(required=False, allow_null=True)
    em_branco = serializers.BooleanField(default=False)

    def validate(self, data):
        try:
            eleicao = Eleicao.objects.get(id=data['eleicao_id'])
        except Eleicao.DoesNotExist:
            raise serializers.ValidationError("Eleição não Existe.")
            
        if eleicao.status != 'aberta':
            raise serializers.ValidationError("Eleição fechada.")

        agora = timezone.now()
        if not (eleicao.data_inicio <= agora <= eleicao.data_fim):
            raise serializers.ValidationError("Não pode mais votar.")

        if not AptidaoEleitor.objects.filter(eleicao_id=data['eleicao_id'], eleitor_id=data['eleitor_id']).exists():
            raise serializers.ValidationError("não está na lista de aptos nesta eleição.")

        if RegistroVotacao.objects.filter(eleicao_id=data['eleicao_id'], eleitor_id=data['eleitor_id']).exists():
            raise serializers.ValidationError("eleitor já registrou voto nesta eleição.")
        candidato_id = data.get('candidato_id')
        em_branco = data.get('em_branco')

        if not (bool(candidato_id) ^ bool(em_branco)):
            raise serializers.ValidationError("Informa candidato ou o voto em branco")

        if candidato_id:
            if not Candidato.objects.filter(id=candidato_id, eleicao_id=data['eleicao_id']).exists():
                raise serializers.ValidationError("Candidato não é desta eleição.")

        return data