# -*- coding: utf-8 -*-
"""Fila FIFO com um único worker: há um só PJe-Calc e uma só pasta de download por máquina."""
import threading
import traceback
from collections import deque

from servico import banco, executor


class GerenciadorFila:

    def __init__(self):
        self._pendentes = deque()
        self._condicao = threading.Condition()
        self._executando = None
        self._thread = None

    def iniciar(self, ids_recuperados):
        with self._condicao:
            self._pendentes.extend(ids_recuperados)
        self._thread = threading.Thread(target=self._laco, name="pjecalc-worker", daemon=True)
        self._thread.start()

    def enfileirar(self, execucao_id):
        with self._condicao:
            self._pendentes.append(execucao_id)
            self._condicao.notify()
            return len(self._pendentes)

    def posicao(self, execucao_id):
        with self._condicao:
            if execucao_id == self._executando:
                return 0
            try:
                return self._pendentes.index(execucao_id) + 1
            except ValueError:
                return None

    def cancelar(self, execucao_id):
        with self._condicao:
            if execucao_id not in self._pendentes:
                return False
            self._pendentes.remove(execucao_id)
        banco.atualizar(
            execucao_id, status=banco.STATUS_CANCELADO,
            mensagem="Cancelada antes de iniciar.", concluido_em=banco.agora(),
        )
        return True

    def estado(self):
        with self._condicao:
            return {
                "executando": self._executando,
                "na_fila": list(self._pendentes),
                "worker_ativo": bool(self._thread and self._thread.is_alive()),
            }

    def _laco(self):
        while True:
            with self._condicao:
                while not self._pendentes:
                    self._condicao.wait()
                execucao_id = self._pendentes.popleft()
                self._executando = execucao_id
            try:
                executor.executar(execucao_id)
            except Exception:
                traceback.print_exc()
                banco.atualizar(
                    execucao_id, status=banco.STATUS_FALHOU, mensagem="Erro interno do serviço.",
                    erro=traceback.format_exc(), concluido_em=banco.agora(),
                )
            finally:
                with self._condicao:
                    self._executando = None


gerenciador = GerenciadorFila()
