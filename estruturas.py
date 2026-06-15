# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------
# MÓDULO: estruturas.py
# --------------------------------------------------------------------------
# RESPONSABILIDADE:
# - Definir as estruturas de dados customizadas do projeto, como o
#   molde para um segmento de came.
# --------------------------------------------------------------------------

# MÓDULO: estruturas.py 

from dataclasses import dataclass

@dataclass
class SegmentoCame:
    """Representa um único trecho (segmento) puramente geométrico do came."""
    tipo: str               # 'subida', 'descida' ou 'parada'
    theta_inicio: float       # Ângulo de início em graus
    theta_fim: float          # Ângulo de fim em graus
    S_inicio: float           # Posição inicial do seguidor para este trecho
    H: float                  # Magnitude da elevação/descida (0 para parada)

    @property
    def beta(self) -> float:
        """Calcula e retorna a duração angular (beta) do segmento em graus."""
        return self.theta_fim - self.theta_inicio

    # O @dataclass gera automaticamente os métodos:
    # __init__(self, tipo, ...): O construtor da classe.
    # __repr__(self): Uma representação textual do objeto, ótima para debug.
    #   É por isso que o `print(seg)` no orquestrador funcionará tão bem.
    # __eq__(self, other): Para comparar dois objetos.
