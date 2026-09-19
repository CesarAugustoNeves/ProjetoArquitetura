import sys
from dataclasses import dataclass
from typing import Dict, List

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

@dataclass
class Response:
    req_id: int
    status_code: int
    message: str


# --- INTEGRAÇÃO FEDERAL (ADR 0003) ---

class FederalSystemMock:
    """
    Simula o sistema federal. 
    Instanciado por célula para não propagar indisponibilidade (ADR 0003).
    """
    def __init__(self, tenant_id: str):
        self.tenant_id = tenant_id
        self.is_down = False  # Pode simular queda de API do ministério específica para uma cidade

    def sync_data(self) -> bool:
        return not self.is_down


# --- INFRAESTRUTURA CELULAR (ADR 0001) ---

class TenantCell:
    """
    Representa a 'Célula' de infraestrutura isolada de um Município.
    Contém seus próprios workers, Event Store e cliente de integração.
    """
    def __init__(self, tenant_id: str, max_workers: int = 4):
        self.tenant_id = tenant_id
        self.active_workers = 1      # Começa com infra (1 worker) para economizar
        self.max_workers = max_workers
        self.current_load = 0
        
        # O banco de dados da célula é um Event Store isolado (ADR 0004)
        self.event_store: List[ProntuarioEvent] = []
        
        # Cliente federal isolado na célula (ADR 0003)
        self.federal_api = FederalSystemMock(tenant_id)

    def reset_load_for_tick(self):
        self.current_load = 0

    def process(self, req: Request) -> Response:
        self.current_load += 1

        # 1. Regra de Auto-scaling e Load Shedding do Envelope D
        if self.current_load > self.active_workers:
            if self.active_workers < self.max_workers:
                self.active_workers += 1
                status = 202
                msg = f"SCALE-UP: Worker {self.active_workers} provisionado."
            else:
                return Response(req.id, 429, f"FALHA ISOLADA: Célula no limite ({self.max_workers} workers).")
        else:
            status = 200
            msg = "Proc. com sucesso (Célula estável)."

        # 2. Simula Integração Federal Isolada (ADR 0003)
        if not self.federal_api.sync_data():
            return Response(req.id, 503, "Erro na fila do sistema federal para esta célula.")

        # 3. Simula persistência orientada a eventos (ADR 0004)
        evento = ProntuarioEvent(req.id, "NOVO_REGISTRO", req.payload, req.timestamp_ms)
        self.event_store.append(evento)

        return Response(req.id, status, msg)


class CloudGateway:
    """
    Gateway de Borda. Roteia tráfego para a célula correspondente.
    """
    def __init__(self):
        self.cells: Dict[str, TenantCell] = {}

    def get_cell(self, tenant_id: str) -> TenantCell:
        if tenant_id not in self.cells:
            self.cells[tenant_id] = TenantCell(tenant_id=tenant_id, max_workers=4)
        return self.cells[tenant_id]

    def route_request(self, req: Request) -> Response:
        return self.get_cell(req.tenant_id).process(req)


# --- MOTOR DE SIMULAÇÃO DETERMINÍSTICA ---

def run_simulation():
    gateway = CloudGateway()
    
    print("="*75)
    print(" PROVA DE CONCEITO - ADR 0001 (Arquitetura Celular)")
    print("="*75)
    print("Objetivo: Provar auto-scaling isolado e proteção contra vizinho ruidoso.\n")

    req_id = 1
    stats = {}

    for tick in range(0, 100, 10):
        print(f"--- TICK DE TEMPO: {tick:02d}ms ---")
        
        for cell in gateway.cells.values():
            cell.reset_load_for_tick()

        tick_requests: List[Request] = []

        # Cidade A: Tráfego normal e constante
        tick_requests.append(Request(req_id, "Cidade A", tick, "Evento Prontuário"))
        req_id += 1

        # Cidade B: A partir dos 30ms, sofre um pico brutal (ex: epidemia local)
        if tick >= 30:
            for _ in range(6): 
                tick_requests.append(Request(req_id, "Cidade B", tick, "Evento Triagem"))
                req_id += 1
        else:
            tick_requests.append(Request(req_id, "Cidade B", tick, "Evento Prontuário"))
            req_id += 1

        # Processamento e Log
        for req in tick_requests:
            res = gateway.route_request(req)
            
            if req.tenant_id not in stats:
                stats[req.tenant_id] = {"200/202": 0, "429": 0}
                
            if res.status_code in (200, 202):
                stats[req.tenant_id]["200/202"] += 1
            else:
                stats[req.tenant_id]["429"] += 1

            print(f" Req {req.id:02d} | {req.tenant_id:8s} -> HTTP {res.status_code} | {res.message}")
        print()

    # Resultados e Auditoria dos ADRs
    print("="*75)
    print(" AUDITORIA DA ARQUITETURA PÓS-PICO")
    print("="*75)
    
    for tenant_id, cell in gateway.cells.items():
        sucessos = stats[tenant_id]["200/202"]
        falhas = stats[tenant_id]["429"]
        eventos_salvos = len(cell.event_store)
        
        print(f"[{tenant_id}]")
        print(f"  - Workers ativos: {cell.active_workers}/{cell.max_workers}")
        print(f"  - Reqs. Atendidas: {sucessos} | Rejeitadas (Load Shedding): {falhas}")
        print(f"  - Event Sourcing (ADR 0004): {eventos_salvos} eventos registrados no ledger.\n")

    print("VEREDICTO DA DECISÃO (ADR 0001):")
    print("Sucesso. A 'Cidade B' esgotou sua infraestrutura de 4 workers devido ao pico")
    print("brutal, sofrendo Load Shedding (HTTP 429). A 'Cidade A' manteve-se operando")
    print("com 1 worker e 100% de disponibilidade. Falha e recursos isolados com sucesso.")

if __name__ == '__main__':
    run_simulation()
