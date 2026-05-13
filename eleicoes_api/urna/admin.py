from django.contrib import admin
from .models import Eleitor, Eleicao, Candidato, Voto, AptidaoEleitor, RegistroVotacao

# Register your models here.

admin.site.register(Eleitor)
admin.site.register(Eleicao)
admin.site.register(Candidato)
admin.site.register(Voto)
admin.site.register(AptidaoEleitor)
admin.site.register(RegistroVotacao)