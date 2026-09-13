import math
from datetime import datetime, timedelta


class SpacedRepetitionService:
    EF_INICIAL = 2.5
    EF_MINIMO = 1.3

    def avaliar(self, fator_facilidade: float, intervalo_atual: int, repeticoes: int, qualidade: int) -> dict:
        if qualidade < 3:
            repeticoes_novo = 0
            intervalo_novo = 1
        else:
            if repeticoes == 0:
                intervalo_novo = 1
            elif repeticoes == 1:
                intervalo_novo = 6
            else:
                intervalo_novo = math.ceil(intervalo_atual * fator_facilidade)
            repeticoes_novo = repeticoes + 1

        ef_novo = fator_facilidade + (0.1 - (5 - qualidade) * (0.08 + (5 - qualidade) * 0.02))
        ef_novo = max(self.EF_MINIMO, ef_novo)

        return {
            "fator_facilidade": ef_novo,
            "intervalo_atual": intervalo_novo,
            "repeticoes": repeticoes_novo,
            "proxima_revisao": datetime.utcnow() + timedelta(days=intervalo_novo),
        }
