import sys
from dataclasses import dataclass
from typing import Dict, List

sys.stdout.reconfigure(encoding="utf-8")  # evita mojibake ao redirecionar no Windows

# --- ESTRUTURAS DE DADOS E EVENT SOURCING (ADR 0004) ---

@dataclass
class ProntuarioEvent:
    """Representa um evento imutável no Event Store (ADR 0004)"""
    req_id: int
    evento_tipo: str
    payload: str
    timestamp_ms: int

@dataclass
class Request:
    id: int
    tenant_id: str
    timestamp_ms: int
    payload: str
    tipo: str  # "TRIAGEM" (local-first, sempre aceito) ou "RESERVA_LEITO" (operação central, síncrona, exclusiva)

@dataclass
class Response:
    req_id: int
    status_code: int
    message: str


# --- INTEGRAÇÃO FEDERAL (ADR 0003) ---

class FederalSystemMock:
    """
    Simula o sistema federal.
    Instanciado por shard de célula para não propagar indisponibilidade (ADR 0003).
    """
    def __init__(self, tenant_id: str):
        self.tenant_id = tenant_id
        self.is_down = False  # Pode simular queda de API do ministério específica para uma cidade

    def sync_data(self) -> bool:
        return not self.is_down


# --- CLIENTE LOCAL DE TRIAGEM (correção da objeção 2) ---

class ClienteLocalTriagem:
    """
    Representa o Cliente Local de Atendimento (Desktop/SQLite) de uma UPA/UBS.

    Grava o evento de triagem localmente primeiro, sem depender da rede nem
    da capacidade do backend central — por isso este caminho NUNCA é
    rejeitado por saturação. Saturação é um problema do backend; a triagem
    não passa por ele para ser aceita. Isso é mais forte que simplesmente
    enfileirar com 202 Accepted, porque sobrevive também a uma queda total
    de rede, não só a uma sobrecarga do servidor.
    """
    def __init__(self, tenant_id: str):
        self.tenant_id = tenant_id
        self.eventos_locais: List[ProntuarioEvent] = []

    def registrar(self, req: Request) -> Response:
        evento = ProntuarioEvent(req.id, "TRIAGEM_REGISTRADA", req.payload, req.timestamp_ms)
        self.eventos_locais.append(evento)
        return Response(req.id, 201, "Triagem registrada localmente (Cliente Local, sem depender do backend).")


# --- SHARD DE CAPACIDADE ELÁSTICA (ADR 0001 + seção 13.2 do livro) ---

class TenantCellShard:
    """
    Atende operações centrais síncronas e exclusivas de um município — ex.:
    reserva de leito, que exige um único escritor por capacidade (ADR 0002).

    Tem um limite de tamanho declarado (max_workers), igual à seção 13.2 do
    livro: "unidade de escala com capacidade máxima declarada". Diferente do
    spike anterior, o shard sozinho nunca decide rejeitar por estar cheio —
    quem decide isso é o Município, criando outro shard (ver Municipio).
    """
    def __init__(self, tenant_id: str, shard_id: int, max_workers: int = 4):
        self.tenant_id = tenant_id
        self.shard_id = shard_id
        self.active_workers = 1       # Começa pequeno, para economizar
        self.max_workers = max_workers
        self.current_load = 0
        self.event_store: List[ProntuarioEvent] = []
        self.federal_api = FederalSystemMock(tenant_id)

    def reset_load_for_tick(self):
        self.current_load = 0

    def tem_capacidade(self) -> bool:
        return self.current_load < self.max_workers

    def processar(self, req: Request) -> Response:
        self.current_load += 1

        if self.active_workers < self.current_load:
            self.active_workers = self.current_load
            status = 202
            msg = f"SCALE-UP: shard {self.shard_id} com {self.active_workers} workers."
        else:
            status = 200
            msg = f"Proc. com sucesso (shard {self.shard_id} estável)."

        if not self.federal_api.sync_data():
            return Response(req.id, 503, f"Erro na fila do sistema federal (shard {self.shard_id}).")

        evento = ProntuarioEvent(req.id, req.tipo, req.payload, req.timestamp_ms)
        self.event_store.append(evento)
        return Response(req.id, status, msg)


# --- MUNICÍPIO: UM CLIENTE LOCAL (triagem) + N SHARDS ELÁSTICOS (operação central) ---

class Municipio:
    """
    Representa a célula de um município (ADR 0001) como ela de fato se
    comporta sob carga: um caminho de triagem que nunca satura (Cliente
    Local) e um caminho de operação central que satura e, ao saturar, tenta
    crescer por célula em vez de rejeitar — seção 13.2: "Atingido o limite,
    cria-se outra célula em vez de aumentar a existente".

    `max_shards` é o teto do próprio município. Só quando esse teto também
    está esgotado é que a operação central volta a receber HTTP 429 — a
    válvula de segurança explícita que a resposta à objeção 2 prometeu
    manter para reserva síncrona exclusiva, nunca para triagem.
    """
    def __init__(self, tenant_id: str, max_workers_por_shard: int = 4, max_shards: int = 2):
        self.tenant_id = tenant_id
        self.cliente_local = ClienteLocalTriagem(tenant_id)
        self.max_workers_por_shard = max_workers_por_shard
        self.max_shards = max_shards
        self.shards: List[TenantCellShard] = [TenantCellShard(tenant_id, 1, max_workers_por_shard)]

    def reset_load_for_tick(self):
        for shard in self.shards:
            shard.reset_load_for_tick()

    def _processar_operacao_central(self, req: Request) -> Response:
        for shard in self.shards:
            if shard.tem_capacidade():
                return shard.processar(req)

        if len(self.shards) < self.max_shards:
            novo_shard = TenantCellShard(self.tenant_id, len(self.shards) + 1, self.max_workers_por_shard)
            self.shards.append(novo_shard)
            return novo_shard.processar(req)

        return Response(
            req.id, 429,
            f"FALHA ISOLADA: município {self.tenant_id} no teto de {self.max_shards} shards."
        )

    def rotear(self, req: Request) -> Response:
        if req.tipo == "TRIAGEM":
            return self.cliente_local.registrar(req)
        return self._processar_operacao_central(req)


class CloudGateway:
    """
    Gateway de Borda. Roteia tráfego para o município correspondente.
    """
    def __init__(self):
        self.municipios: Dict[str, Municipio] = {}

    def get_municipio(self, tenant_id: str) -> Municipio:
        if tenant_id not in self.municipios:
            self.municipios[tenant_id] = Municipio(tenant_id)
        return self.municipios[tenant_id]

    def route_request(self, req: Request) -> Response:
        return self.get_municipio(req.tenant_id).rotear(req)


# --- MOTOR DE SIMULAÇÃO DETERMINÍSTICA ---

def run_simulation():
    gateway = CloudGateway()

    print("=" * 83)
    print(" PROVA DE CONCEITO - ADR 0001 (Arquitetura Celular) + correção da objeção 2")
    print("=" * 83)
    print("Objetivo: provar que triagem nunca é rejeitada, e que a saturação de operação")
    print("central provisiona célula nova antes de recorrer ao HTTP 429.\n")

    req_id = 1
    stats = {}

    def registrar_stat(tenant_id: str, tipo: str, status_code: int):
        s = stats.setdefault(tenant_id, {
            "TRIAGEM_200/201": 0, "TRIAGEM_429": 0,
            "RESERVA_200/202": 0, "RESERVA_429": 0,
        })
        if tipo == "TRIAGEM":
            s["TRIAGEM_200/201" if status_code != 429 else "TRIAGEM_429"] += 1
        else:
            s["RESERVA_200/202" if status_code != 429 else "RESERVA_429"] += 1

    for tick in range(0, 100, 10):
        print(f"--- TICK DE TEMPO: {tick:02d}ms ---")

        for municipio in gateway.municipios.values():
            municipio.reset_load_for_tick()

        tick_requests: List[Request] = []

        # Cidade A: tráfego normal e constante (triagem + uma reserva ocasional)
        tick_requests.append(Request(req_id, "Cidade A", tick, "Evento Prontuário", "TRIAGEM"))
        req_id += 1

        # Cidade B: a partir dos 30ms, pico brutal de triagem (ex.: epidemia local)
        if tick >= 30:
            for _ in range(6):
                tick_requests.append(Request(req_id, "Cidade B", tick, "Evento Triagem", "TRIAGEM"))
                req_id += 1
            # Junto do pico, reservas de leito também sobem: mostra o shard novo sendo criado
            for _ in range(5):
                tick_requests.append(Request(req_id, "Cidade B", tick, "Reserva de leito", "RESERVA_LEITO"))
                req_id += 1
        else:
            tick_requests.append(Request(req_id, "Cidade B", tick, "Evento Prontuário", "TRIAGEM"))
            req_id += 1

        # No pico máximo (90ms), uma rajada extrema de reservas para provar que a
        # válvula de segurança (HTTP 429) continua existindo quando até os shards
        # elásticos se esgotam — ela só deixou de ser a PRIMEIRA resposta à saturação.
        if tick == 90:
            for _ in range(6):
                tick_requests.append(Request(req_id, "Cidade B", tick, "Reserva de leito (rajada extrema)", "RESERVA_LEITO"))
                req_id += 1

        for req in tick_requests:
            res = gateway.route_request(req)
            registrar_stat(req.tenant_id, req.tipo, res.status_code)
            print(f" Req {req.id:02d} | {req.tenant_id:8s} | {req.tipo:13s} -> HTTP {res.status_code} | {res.message}")
        print()

    print("=" * 83)
    print(" AUDITORIA DA ARQUITETURA PÓS-PICO")
    print("=" * 83)

    for tenant_id, municipio in gateway.municipios.items():
        s = stats[tenant_id]
        eventos_triagem = len(municipio.cliente_local.eventos_locais)
        eventos_central = sum(len(shard.event_store) for shard in municipio.shards)

        print(f"[{tenant_id}]")
        print(f"  - Triagem local: {s['TRIAGEM_200/201']} aceitas | {s['TRIAGEM_429']} rejeitadas "
              f"({eventos_triagem} eventos no Cliente Local)")
        print(f"  - Reserva de leito (operação central): {s['RESERVA_200/202']} aceitas | "
              f"{s['RESERVA_429']} rejeitadas (válvula de segurança)")
        print(f"  - Shards ativos: {len(municipio.shards)}/{municipio.max_shards} "
              f"({eventos_central} eventos gravados no total)\n")

    print("VEREDICTO DA DECISÃO (ADR 0001 + correção da objeção 2):")
    print("Sucesso. A triagem da Cidade B nunca foi rejeitada, mesmo no pico brutal, porque")
    print("não depende da capacidade do backend (Cliente Local). A reserva de leito, que É")
    print("síncrona e exclusiva, saturou o primeiro shard e provisionou um segundo — seção")
    print("13.2 do livro — em vez de rejeitar de imediato. Só na rajada extrema de 90ms,")
    print("acima da capacidade de 2 shards, o HTTP 429 voltou a aparecer: a válvula de")
    print("segurança explícita continua existindo, mas deixou de ser a primeira resposta.")

if __name__ == '__main__':
    run_simulation()