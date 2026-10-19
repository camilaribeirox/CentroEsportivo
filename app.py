#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
================================================================================
SISTEMA DE GESTÃO DE CENTRO ESPORTIVO
================================================================================
Disciplina: Banco de Dados 2 - IFSP Jacareí (ADS)
Prof. Raul E. S. Castanhari

Arquitetura em Camadas (Baseada nos Slides e Relatório Técnico):
  1. Camada de Apresentação: InteracaoUsuario (CLI Terminal)
  2. Camada de Controle:      Controlador (Regras de Negócio e Validações)
  3. Camada de Domínio:       Classes de Entidade (Modalidade, Instrutor, Aluno,
                              MatriculaModalidade, ExameMedico)
  4. Camada de Persistência:  AdaptadorMapaObjetoRelacional (ORM / SQLite)
================================================================================
"""

import os
import sys
import re
import sqlite3
import datetime
from typing import List, Dict, Optional, Tuple, Any

# Habilita cores ANSI no console do Windows
if sys.platform == "win32":
    try:
        import ctypes
        kernel32 = ctypes.windll.kernel32
        kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)
    except Exception:
        pass

# Constantes de Estilização ANSI
class Cores:
    RESET = "\033[0m"
    NEGRITO = "\033[1m"
    DIM = "\033[2m"
    ITALICO = "\033[3m"
    SUBLINHADO = "\033[4m"

    # Cores de texto
    VERMELHO = "\033[91m"
    VERDE = "\033[92m"
    AMARELO = "\033[93m"
    AZUL = "\033[94m"
    MAGENTA = "\033[95m"
    CIANO = "\033[96m"
    BRANCO = "\033[97m"

    # Fundos
    BG_AZUL = "\033[44m"
    BG_VERDE = "\033[42m"
    BG_MAGENTA = "\033[45m"
    BG_CIANO = "\033[46m"


# ==============================================================================
# CAMADA 3: CLASSES DE ENTIDADE (DOMÍNIO)
# ==============================================================================

class Modalidade:
    """Entidade que representa um esporte oferecido e seu preço mensal."""
    def __init__(self, id_modalidade: Optional[int], nome_modalidade: str, preco_mensal: float):
        self.id_modalidade = id_modalidade
        self.nome_modalidade = nome_modalidade.strip()
        self.preco_mensal = float(preco_mensal)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id_modalidade": self.id_modalidade,
            "nome_modalidade": self.nome_modalidade,
            "preco_mensal": self.preco_mensal
        }

    def __repr__(self) -> str:
        return f"<Modalidade #{self.id_modalidade}: {self.nome_modalidade} (R$ {self.preco_mensal:.2f})>"


class Aluno:
    """Entidade que representa um aluno matriculado com CPF e data de registro."""
    def __init__(self, id_aluno: Optional[int], nome_aluno: str, cpf: str, data_matricula: str):
        self.id_aluno = id_aluno
        self.nome_aluno = nome_aluno.strip()
        self.cpf = "".join(filter(str.isdigit, str(cpf)))
        self.data_matricula = data_matricula.strip()

    def cpf_formatado(self) -> str:
        if len(self.cpf) == 11:
            return f"{self.cpf[:3]}.{self.cpf[3:6]}.{self.cpf[6:9]}-{self.cpf[9:]}"
        return self.cpf

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id_aluno": self.id_aluno,
            "nome_aluno": self.nome_aluno,
            "cpf": self.cpf,
            "data_matricula": self.data_matricula
        }

    def __repr__(self) -> str:
        return f"<Aluno #{self.id_aluno}: {self.nome_aluno} (CPF: {self.cpf})>"


class Instrutor:
    """Entidade que representa um instrutor de uma modalidade específica (1:N)."""
    def __init__(self, id_instrutor: Optional[int], nome_instrutor: str, cref: str, id_modalidade: int):
        self.id_instrutor = id_instrutor
        self.nome_instrutor = nome_instrutor.strip()
        self.cref = cref.strip().upper()
        self.id_modalidade = int(id_modalidade)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id_instrutor": self.id_instrutor,
            "nome_instrutor": self.nome_instrutor,
            "cref": self.cref,
            "id_modalidade": self.id_modalidade
        }

    def __repr__(self) -> str:
        return f"<Instrutor #{self.id_instrutor}: {self.nome_instrutor} (CREF: {self.cref}, Mod: {self.id_modalidade})>"


class MatriculaModalidade:
    """Entidade associativa que conecta Alunos e Modalidades (N:N) com data de adesão."""
    def __init__(self, id_matricula_modalidade: Optional[int], data_adesao: str, id_modalidade: int, id_aluno: int):
        self.id_matricula_modalidade = id_matricula_modalidade
        self.data_adesao = data_adesao.strip()
        self.id_modalidade = int(id_modalidade)
        self.id_aluno = int(id_aluno)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id_matricula_modalidade": self.id_matricula_modalidade,
            "data_adesao": self.data_adesao,
            "id_modalidade": self.id_modalidade,
            "id_aluno": self.id_aluno
        }

    def __repr__(self) -> str:
        return f"<Matricula #{self.id_matricula_modalidade}: Aluno {self.id_aluno} -> Modalidade {self.id_modalidade} em {self.data_adesao}>"


class ExameMedico:
    """Entidade que registra o laudo médico estritamente único por aluno (1:1)."""
    def __init__(self, id_exame: Optional[int], data_avaliacao: str, situacao: str, id_aluno: int):
        self.id_exame = id_exame
        self.data_avaliacao = data_avaliacao.strip()
        self.situacao = situacao.strip().capitalize()
        self.id_aluno = int(id_aluno)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id_exame": self.id_exame,
            "data_avaliacao": self.data_avaliacao,
            "situacao": self.situacao,
            "id_aluno": self.id_aluno
        }

    def __repr__(self) -> str:
        return f"<ExameMedico #{self.id_exame}: Aluno {self.id_aluno} - {self.situacao} em {self.data_avaliacao}>"


# ==============================================================================
# CAMADA 4: ADAPTADOR MAPA OBJETO-RELACIONAL (ORM / PERSISTÊNCIA)
# ==============================================================================

class AdaptadorMapaObjetoRelacional:
    """
    Componente responsável por serializar objetos em registros SQL e
    desserializar tuplas relacionais em objetos de negócio, eliminando a
    incompatibilidade de impedância (Opção 6, Aula 9).
    """

    def __init__(self, db_path: str = "centro_esportivo.db"):
        self.db_path = db_path
        self._inicializar_banco()

    def get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        # Ativa suporte estrito a chaves estrangeiras no SQLite
        conn.execute("PRAGMA foreign_keys = ON;")
        conn.row_factory = sqlite3.Row
        return conn

    def _inicializar_banco(self):
        """Cria o esquema relacional com chaves, índices e restrições se não existirem."""
        with self.get_connection() as conn:
            cur = conn.cursor()
            cur.executescript("""
            CREATE TABLE IF NOT EXISTS Modalidades (
                id_modalidade INTEGER PRIMARY KEY AUTOINCREMENT,
                nome_modalidade TEXT NOT NULL,
                preco_mensal REAL NOT NULL CHECK (preco_mensal >= 0)
            );

            CREATE TABLE IF NOT EXISTS Alunos (
                id_aluno INTEGER PRIMARY KEY AUTOINCREMENT,
                nome_aluno TEXT NOT NULL,
                cpf TEXT NOT NULL UNIQUE,
                data_matricula TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS Instrutores (
                id_instrutor INTEGER PRIMARY KEY AUTOINCREMENT,
                nome_instrutor TEXT NOT NULL,
                cref TEXT NOT NULL UNIQUE,
                id_modalidade INTEGER NOT NULL,
                FOREIGN KEY (id_modalidade) REFERENCES Modalidades(id_modalidade)
                    ON UPDATE CASCADE ON DELETE RESTRICT
            );

            CREATE TABLE IF NOT EXISTS ExamesMedicos (
                id_exame INTEGER PRIMARY KEY AUTOINCREMENT,
                data_avaliacao TEXT NOT NULL,
                situacao TEXT NOT NULL CHECK (situacao IN ('Apto', 'Inapto')),
                id_aluno INTEGER NOT NULL UNIQUE,
                FOREIGN KEY (id_aluno) REFERENCES Alunos(id_aluno)
                    ON UPDATE CASCADE ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS MatriculasModalidades (
                id_matricula_modalidade INTEGER PRIMARY KEY AUTOINCREMENT,
                data_adesao TEXT NOT NULL,
                id_modalidade INTEGER NOT NULL,
                id_aluno INTEGER NOT NULL,
                FOREIGN KEY (id_modalidade) REFERENCES Modalidades(id_modalidade)
                    ON UPDATE CASCADE ON DELETE CASCADE,
                FOREIGN KEY (id_aluno) REFERENCES Alunos(id_aluno)
                    ON UPDATE CASCADE ON DELETE CASCADE,
                UNIQUE (id_aluno, id_modalidade)
            );
            """)

            # Se o banco estiver vazio, carrega automaticamente os 27 registros dos slides
            cur.execute("SELECT COUNT(*) FROM Modalidades")
            if cur.fetchone()[0] == 0:
                self.carregar_dados_iniciais(conn)

    def carregar_dados_iniciais(self, conn: Optional[sqlite3.Connection] = None):
        """Popula a base com os 27 registros oficiais documentados no trabalho."""
        should_close = False
        if conn is None:
            conn = self.get_connection()
            should_close = True

        try:
            cur = conn.cursor()

            # 5 Modalidades
            modalidades = [
                (1, "Musculação", 90.00),
                (2, "Crossfit", 150.00),
                (3, "Natação", 150.00),
                (4, "Pilates", 130.00),
                (5, "Boxe", 110.00)
            ]
            cur.executemany("INSERT OR REPLACE INTO Modalidades (id_modalidade, nome_modalidade, preco_mensal) VALUES (?, ?, ?);", modalidades)

            # 5 Alunos
            alunos = [
                (1, "Helena Vieira", "99988877766", "2026-01-10"),
                (2, "Camila Ribeiro", "44433322211", "2026-02-15"),
                (3, "Jeremias Souza", "11122233344", "2026-03-30"),
                (4, "Lucas Silva", "55566677788", "2026-04-10"),
                (5, "Beatriz Lima", "22233344455", "2026-05-15")
            ]
            cur.executemany("INSERT OR REPLACE INTO Alunos (id_aluno, nome_aluno, cpf, data_matricula) VALUES (?, ?, ?, ?);", alunos)

            # 5 Instrutores
            instrutores = [
                (1, "Professora Maria Clara Pastor", "CREF/SP 11111", 2),
                (2, "Professor Caio Polidoro", "CREF/SP 22222", 1),
                (3, "Professor Marcelo Costa", "CREF/SP 33333", 3),
                (4, "Professora Fernanda Souza", "CREF/SP 44444", 4),
                (5, "Professor Rodrigo Alves", "CREF/SP 55555", 5)
            ]
            cur.executemany("INSERT OR REPLACE INTO Instrutores (id_instrutor, nome_instrutor, cref, id_modalidade) VALUES (?, ?, ?, ?);", instrutores)

            # 5 Exames Médicos
            exames = [
                (1, "2026-01-09", "Apto", 1),
                (2, "2026-02-14", "Apto", 2),
                (3, "2026-04-14", "Inapto", 3),
                (4, "2026-04-09", "Apto", 4),
                (5, "2026-05-14", "Apto", 5)
            ]
            cur.executemany("INSERT OR REPLACE INTO ExamesMedicos (id_exame, data_avaliacao, situacao, id_aluno) VALUES (?, ?, ?, ?);", exames)

            # 7 Matrículas Associativas
            matriculas = [
                (1, "2026-01-10", 1, 1),
                (2, "2026-01-20", 2, 1),
                (3, "2026-02-15", 2, 2),
                (4, "2026-05-15", 3, 3),
                (5, "2026-04-10", 1, 4),
                (6, "2026-04-12", 3, 4),
                (7, "2026-05-15", 4, 5)
            ]
            cur.executemany("INSERT OR REPLACE INTO MatriculasModalidades (id_matricula_modalidade, data_adesao, id_modalidade, id_aluno) VALUES (?, ?, ?, ?);", matriculas)

            conn.commit()
        finally:
            if should_close:
                conn.close()

    def resetar_banco(self):
        """Limpa as tabelas e restaura rigorosamente os 27 registros dos slides."""
        with self.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("PRAGMA foreign_keys = OFF;")
            cur.execute("DROP TABLE IF EXISTS MatriculasModalidades;")
            cur.execute("DROP TABLE IF EXISTS ExamesMedicos;")
            cur.execute("DROP TABLE IF EXISTS Instrutores;")
            cur.execute("DROP TABLE IF EXISTS Alunos;")
            cur.execute("DROP TABLE IF EXISTS Modalidades;")
            cur.execute("PRAGMA foreign_keys = ON;")
            conn.commit()
        self._inicializar_banco()

    # --- MÉTODOS DE MODALIDADES ---
    def inserir_modalidade(self, modalidade: Modalidade) -> int:
        with self.get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO Modalidades (nome_modalidade, preco_mensal) VALUES (?, ?);",
                (modalidade.nome_modalidade, modalidade.preco_mensal)
            )
            conn.commit()
            return cur.lastrowid

    def listar_modalidades(self) -> List[Modalidade]:
        with self.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT id_modalidade, nome_modalidade, preco_mensal FROM Modalidades ORDER BY id_modalidade ASC;")
            rows = cur.fetchall()
            return [Modalidade(r["id_modalidade"], r["nome_modalidade"], r["preco_mensal"]) for r in rows]

    def buscar_modalidade(self, id_modalidade: int) -> Optional[Modalidade]:
        with self.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT id_modalidade, nome_modalidade, preco_mensal FROM Modalidades WHERE id_modalidade = ?;", (id_modalidade,))
            r = cur.fetchone()
            if r:
                return Modalidade(r["id_modalidade"], r["nome_modalidade"], r["preco_mensal"])
            return None

    def atualizar_modalidade(self, modalidade: Modalidade) -> bool:
        with self.get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                "UPDATE Modalidades SET nome_modalidade = ?, preco_mensal = ? WHERE id_modalidade = ?;",
                (modalidade.nome_modalidade, modalidade.preco_mensal, modalidade.id_modalidade)
            )
            conn.commit()
            return cur.rowcount > 0

    def excluir_modalidade(self, id_modalidade: int) -> bool:
        with self.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("DELETE FROM Modalidades WHERE id_modalidade = ?;", (id_modalidade,))
            conn.commit()
            return cur.rowcount > 0

    # --- MÉTODOS DE ALUNOS ---
    def inserir_aluno(self, aluno: Aluno) -> int:
        with self.get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO Alunos (nome_aluno, cpf, data_matricula) VALUES (?, ?, ?);",
                (aluno.nome_aluno, aluno.cpf, aluno.data_matricula)
            )
            conn.commit()
            return cur.lastrowid

    def listar_alunos(self) -> List[Aluno]:
        with self.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT id_aluno, nome_aluno, cpf, data_matricula FROM Alunos ORDER BY id_aluno ASC;")
            rows = cur.fetchall()
            return [Aluno(r["id_aluno"], r["nome_aluno"], r["cpf"], r["data_matricula"]) for r in rows]

    def buscar_aluno(self, id_aluno: int) -> Optional[Aluno]:
        with self.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT id_aluno, nome_aluno, cpf, data_matricula FROM Alunos WHERE id_aluno = ?;", (id_aluno,))
            r = cur.fetchone()
            if r:
                return Aluno(r["id_aluno"], r["nome_aluno"], r["cpf"], r["data_matricula"])
            return None

    def buscar_aluno_por_cpf(self, cpf: str) -> Optional[Aluno]:
        cpf_limpo = "".join(filter(str.isdigit, str(cpf)))
        with self.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT id_aluno, nome_aluno, cpf, data_matricula FROM Alunos WHERE cpf = ?;", (cpf_limpo,))
            r = cur.fetchone()
            if r:
                return Aluno(r["id_aluno"], r["nome_aluno"], r["cpf"], r["data_matricula"])
            return None

    def atualizar_aluno(self, aluno: Aluno) -> bool:
        with self.get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                "UPDATE Alunos SET nome_aluno = ?, cpf = ?, data_matricula = ? WHERE id_aluno = ?;",
                (aluno.nome_aluno, aluno.cpf, aluno.data_matricula, aluno.id_aluno)
            )
            conn.commit()
            return cur.rowcount > 0

    def excluir_aluno(self, id_aluno: int) -> bool:
        with self.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("DELETE FROM Alunos WHERE id_aluno = ?;", (id_aluno,))
            conn.commit()
            return cur.rowcount > 0

    # --- MÉTODOS DE INSTRUTORES ---
    def inserir_instrutor(self, instrutor: Instrutor) -> int:
        with self.get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO Instrutores (nome_instrutor, cref, id_modalidade) VALUES (?, ?, ?);",
                (instrutor.nome_instrutor, instrutor.cref, instrutor.id_modalidade)
            )
            conn.commit()
            return cur.lastrowid

    def listar_instrutores(self) -> List[Dict[str, Any]]:
        with self.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("""
                SELECT i.id_instrutor, i.nome_instrutor, i.cref, i.id_modalidade, m.nome_modalidade
                FROM Instrutores i
                INNER JOIN Modalidades m ON i.id_modalidade = m.id_modalidade
                ORDER BY i.id_instrutor ASC;
            """)
            rows = cur.fetchall()
            return [dict(r) for r in rows]

    def buscar_instrutor(self, id_instrutor: int) -> Optional[Instrutor]:
        with self.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT id_instrutor, nome_instrutor, cref, id_modalidade FROM Instrutores WHERE id_instrutor = ?;", (id_instrutor,))
            r = cur.fetchone()
            if r:
                return Instrutor(r["id_instrutor"], r["nome_instrutor"], r["cref"], r["id_modalidade"])
            return None

    def atualizar_instrutor(self, instrutor: Instrutor) -> bool:
        with self.get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                "UPDATE Instrutores SET nome_instrutor = ?, cref = ?, id_modalidade = ? WHERE id_instrutor = ?;",
                (instrutor.nome_instrutor, instrutor.cref, instrutor.id_modalidade, instrutor.id_instrutor)
            )
            conn.commit()
            return cur.rowcount > 0

    def excluir_instrutor(self, id_instrutor: int) -> bool:
        with self.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("DELETE FROM Instrutores WHERE id_instrutor = ?;", (id_instrutor,))
            conn.commit()
            return cur.rowcount > 0

    # --- MÉTODOS DE MATRÍCULAS (N:N) ---
    def matricular_aluno(self, matricula: MatriculaModalidade) -> int:
        with self.get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO MatriculasModalidades (data_adesao, id_modalidade, id_aluno) VALUES (?, ?, ?);",
                (matricula.data_adesao, matricula.id_modalidade, matricula.id_aluno)
            )
            conn.commit()
            return cur.lastrowid

    def listar_matriculas(self) -> List[Dict[str, Any]]:
        with self.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("""
                SELECT mm.id_matricula_modalidade, mm.data_adesao, mm.id_aluno, a.nome_aluno,
                       mm.id_modalidade, m.nome_modalidade, m.preco_mensal
                FROM MatriculasModalidades mm
                INNER JOIN Alunos a ON mm.id_aluno = a.id_aluno
                INNER JOIN Modalidades m ON mm.id_modalidade = m.id_modalidade
                ORDER BY mm.id_matricula_modalidade ASC;
            """)
            rows = cur.fetchall()
            return [dict(r) for r in rows]

    def cancelar_matricula(self, id_matricula: int) -> bool:
        with self.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("DELETE FROM MatriculasModalidades WHERE id_matricula_modalidade = ?;", (id_matricula,))
            conn.commit()
            return cur.rowcount > 0

    def cancelar_matricula_especifica(self, id_aluno: int, id_modalidade: int) -> bool:
        with self.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("DELETE FROM MatriculasModalidades WHERE id_aluno = ? AND id_modalidade = ?;", (id_aluno, id_modalidade))
            conn.commit()
            return cur.rowcount > 0

    # --- MÉTODOS DE EXAMES MÉDICOS (1:1) ---
    def inserir_ou_atualizar_exame(self, exame: ExameMedico) -> int:
        with self.get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                INSERT INTO ExamesMedicos (data_avaliacao, situacao, id_aluno)
                VALUES (?, ?, ?)
                ON CONFLICT(id_aluno) DO UPDATE SET
                    data_avaliacao = excluded.data_avaliacao,
                    situacao = excluded.situacao;
                """,
                (exame.data_avaliacao, exame.situacao, exame.id_aluno)
            )
            conn.commit()
            return cur.lastrowid

    def listar_exames(self) -> List[Dict[str, Any]]:
        with self.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("""
                SELECT em.id_exame, em.data_avaliacao, em.situacao, em.id_aluno, a.nome_aluno, a.cpf
                FROM ExamesMedicos em
                INNER JOIN Alunos a ON em.id_aluno = a.id_aluno
                ORDER BY em.id_exame ASC;
            """)
            rows = cur.fetchall()
            return [dict(r) for r in rows]

    def buscar_exame_aluno(self, id_aluno: int) -> Optional[ExameMedico]:
        with self.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT id_exame, data_avaliacao, situacao, id_aluno FROM ExamesMedicos WHERE id_aluno = ?;", (id_aluno,))
            r = cur.fetchone()
            if r:
                return ExameMedico(r["id_exame"], r["data_avaliacao"], r["situacao"], r["id_aluno"])
            return None

    def excluir_exame(self, id_exame: int) -> bool:
        with self.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("DELETE FROM ExamesMedicos WHERE id_exame = ?;", (id_exame,))
            conn.commit()
            return cur.rowcount > 0

    # --- AS 4 SELEÇÕES COMPLEXAS DO TRABALHO ---
    def consulta_1_alunos_aptos(self, preco_minimo: float = 90.0) -> List[Dict[str, Any]]:
        """
        Consulta 1: Ficha Geral de Alunos com Exame Apto (Junção de 5 tabelas)
        Cruzamento de Alunos + Matriculas + Modalidades + Instrutores + Exames
        """
        sql = """
        SELECT
            a.nome_aluno AS Aluno,
            a.cpf AS CPF,
            m.nome_modalidade AS Modalidade,
            printf('R$ %.2f', m.preco_mensal) AS Mensalidade,
            i.nome_instrutor AS Instrutor_Responsavel,
            i.cref AS CREF,
            em.situacao AS Situacao_Medica,
            strftime('%d/%m/%Y', mm.data_adesao) AS Data_Adesao
        FROM Alunos a
        INNER JOIN MatriculasModalidades mm ON a.id_aluno = mm.id_aluno
        INNER JOIN Modalidades m ON mm.id_modalidade = m.id_modalidade
        INNER JOIN Instrutores i ON m.id_modalidade = i.id_modalidade
        INNER JOIN ExamesMedicos em ON a.id_aluno = em.id_aluno
        WHERE em.situacao = 'Apto' AND m.preco_mensal >= ?
        ORDER BY a.nome_aluno ASC, m.nome_modalidade ASC;
        """
        with self.get_connection() as conn:
            cur = conn.cursor()
            cur.execute(sql, (preco_minimo,))
            return [dict(r) for r in cur.fetchall()]

    def consulta_2_auditoria_medica_inaptos(self) -> List[Dict[str, Any]]:
        """
        Consulta 2: Auditoria Médica Preventiva (Alunos Inaptos em Atividades Físicas)
        Localiza quem está com matrícula ativa porém reprovado no laudo médico.
        """
        sql = """
        SELECT
            a.id_aluno,
            a.nome_aluno AS Aluno,
            em.situacao AS Status_Exame,
            strftime('%d/%m/%Y', em.data_avaliacao) AS Data_Avaliacao_Medica,
            m.nome_modalidade AS Modalidade_Matriculada,
            i.nome_instrutor AS Instrutor_Avisado
        FROM Alunos a
        INNER JOIN ExamesMedicos em ON a.id_aluno = em.id_aluno
        INNER JOIN MatriculasModalidades mm ON a.id_aluno = mm.id_aluno
        INNER JOIN Modalidades m ON mm.id_modalidade = m.id_modalidade
        INNER JOIN Instrutores i ON m.id_modalidade = i.id_modalidade
        WHERE em.situacao = 'Inapto';
        """
        with self.get_connection() as conn:
            cur = conn.cursor()
            cur.execute(sql)
            return [dict(r) for r in cur.fetchall()]

    def consulta_3_faturamento_por_modalidade(self) -> List[Dict[str, Any]]:
        """
        Consulta 3: Faturamento Estimado e Quantidade de Alunos por Modalidade
        LEFT JOIN + GROUP BY + COUNT + SUM + HAVING > 0
        """
        sql = """
        SELECT
            m.id_modalidade,
            m.nome_modalidade AS Modalidade,
            i.nome_instrutor AS Instrutor,
            printf('R$ %.2f', m.preco_mensal) AS Valor_Unitario,
            COUNT(mm.id_aluno) AS Total_Alunos_Matriculados,
            printf('R$ %.2f', SUM(m.preco_mensal)) AS Receita_Mensal_Gerada
        FROM Modalidades m
        LEFT JOIN Instrutores i ON m.id_modalidade = i.id_modalidade
        LEFT JOIN MatriculasModalidades mm ON m.id_modalidade = mm.id_modalidade
        GROUP BY m.id_modalidade, m.nome_modalidade, i.nome_instrutor, m.preco_mensal
        HAVING COUNT(mm.id_aluno) > 0
        ORDER BY SUM(m.preco_mensal) DESC;
        """
        with self.get_connection() as conn:
            cur = conn.cursor()
            cur.execute(sql)
            return [dict(r) for r in cur.fetchall()]

    def consulta_4_alunos_multidisciplinares(self) -> List[Dict[str, Any]]:
        """
        Consulta 4: Alunos Multidisciplinares e Mensalidade Acumulada
        GROUP BY + COUNT > 1 + GROUP_CONCAT + SUM
        """
        sql = """
        SELECT
            a.id_aluno,
            a.nome_aluno AS Aluno,
            COUNT(mm.id_modalidade) AS Qtd_Modalidades,
            group_concat(m.nome_modalidade, ', ') AS Modalidades_Cursadas,
            printf('R$ %.2f', SUM(m.preco_mensal)) AS Mensalidade_Total_Aluno
        FROM Alunos a
        INNER JOIN MatriculasModalidades mm ON a.id_aluno = mm.id_aluno
        INNER JOIN Modalidades m ON mm.id_modalidade = m.id_modalidade
        GROUP BY a.id_aluno, a.nome_aluno
        HAVING COUNT(mm.id_modalidade) > 1
        ORDER BY SUM(m.preco_mensal) DESC;
        """
        with self.get_connection() as conn:
            cur = conn.cursor()
            cur.execute(sql)
            return [dict(r) for r in cur.fetchall()]

    # --- DEMONSTRAÇÃO DOS SLIDES 15 E 16 ---
    def executar_updates_slide_15(self) -> Dict[str, Any]:
        """
        Executa os 3 UPDATEs documentados no Slide 15:
          1. Reajuste de 10% nas modalidades > R$ 100,00
          2. Liberação médica de Jeremias Souza (id 3) para 'Apto'
          3. Atualização cadastral de Helena Vieira por CPF
        """
        with self.get_connection() as conn:
            cur = conn.cursor()
            # 1. Reajuste
            cur.execute("UPDATE Modalidades SET preco_mensal = round(preco_mensal * 1.10, 2) WHERE preco_mensal > 100.00;")
            af_reajuste = cur.rowcount

            # 2. Liberação médica
            cur.execute("UPDATE ExamesMedicos SET situacao = 'Apto', data_avaliacao = '2026-06-01' WHERE id_aluno = 3;")
            af_exame = cur.rowcount

            # 3. Atualização cadastral
            cur.execute("UPDATE Alunos SET nome_aluno = 'Helena Vieira da Silva' WHERE cpf = '99988877766';")
            af_aluno = cur.rowcount

            conn.commit()
            return {
                "modalidades_reajustadas": af_reajuste,
                "exames_liberados": af_exame,
                "alunos_atualizados": af_aluno
            }

    def executar_deletes_slide_16(self) -> Dict[str, Any]:
        """
        Executa os 2 DELETEs documentados no Slide 16:
          1. Cancela matrícula de Jeremias em Natação (id_aluno = 3, id_modalidade = 3)
          2. Remove a aluna Camila Ribeiro (id_aluno = 2) testando o CASCADE
          3. Verifica se matrículas e exames de Camila foram removidos automaticamente
        """
        with self.get_connection() as conn:
            cur = conn.cursor()
            # 1. Cancelar matrícula
            cur.execute("DELETE FROM MatriculasModalidades WHERE id_aluno = 3 AND id_modalidade = 3;")
            af_mat = cur.rowcount

            # 2. Excluir aluna Camila (id 2)
            cur.execute("DELETE FROM Alunos WHERE id_aluno = 2;")
            af_aluna = cur.rowcount

            # 3. Conferência em cascata
            cur.execute("SELECT COUNT(*) FROM MatriculasModalidades WHERE id_aluno = 2;")
            restantes_mat = cur.fetchone()[0]

            cur.execute("SELECT COUNT(*) FROM ExamesMedicos WHERE id_aluno = 2;")
            restantes_exame = cur.fetchone()[0]

            conn.commit()
            return {
                "matriculas_canceladas": af_mat,
                "alunas_removidas": af_aluna,
                "orfaos_matriculas": restantes_mat,
                "orfaos_exames": restantes_exame
            }


# ==============================================================================
# CAMADA 2: CONTROLADOR (REGRAS DE NEGÓCIO E VALIDAÇÕES)
# ==============================================================================

class RespostaControlador:
    """Objeto padrão de transferência de resposta da camada de controle."""
    def __init__(self, sucesso: bool, mensagem: str, dados: Any = None):
        self.sucesso = sucesso
        self.mensagem = mensagem
        self.dados = dados


class ControladorCentroEsportivo:
    """
    Controlador central da aplicação.
    Coordena as operações de negócio, valida os dados de entrada antes de
    persistir e manipula as regras de integridade relacional.
    """

    def __init__(self, adaptador: Optional[AdaptadorMapaObjetoRelacional] = None):
        self.adaptador = adaptador or AdaptadorMapaObjetoRelacional()

    # --- VALIDAÇÕES AUXILIARES ---
    @staticmethod
    def validar_cpf(cpf: str) -> Tuple[bool, str]:
        cpf_limpo = "".join(filter(str.isdigit, str(cpf)))
        if len(cpf_limpo) != 11:
            return False, "O CPF deve conter exatamente 11 dígitos numéricos."
        return True, cpf_limpo

    @staticmethod
    def validar_data(data_str: str) -> Tuple[bool, str]:
        data_str = data_str.strip()
        formatos = ["%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y"]
        for fmt in formatos:
            try:
                dt = datetime.datetime.strptime(data_str, fmt)
                return True, dt.strftime("%Y-%m-%d")
            except ValueError:
                continue
        return False, "Data inválida. Utilize o formato AAAA-MM-DD ou DD/MM/AAAA."

    # --- GESTÃO DE MODALIDADES ---
    def cadastrar_modalidade(self, nome: str, preco: float) -> RespostaControlador:
        nome = nome.strip()
        if not nome:
            return RespostaControlador(False, "O nome da modalidade não pode ser vazio.")
        if preco < 0:
            return RespostaControlador(False, "O preço mensal deve ser maior ou igual a zero (CHECK positivo).")

        mod = Modalidade(None, nome, preco)
        try:
            mod_id = self.adaptador.inserir_modalidade(mod)
            mod.id_modalidade = mod_id
            return RespostaControlador(True, f"Modalidade '{nome}' cadastrada com sucesso! (ID: {mod_id})", mod)
        except Exception as e:
            return RespostaControlador(False, f"Erro ao persistir modalidade: {e}")

    def atualizar_modalidade(self, id_modalidade: int, novo_nome: str, novo_preco: float) -> RespostaControlador:
        mod = self.adaptador.buscar_modalidade(id_modalidade)
        if not mod:
            return RespostaControlador(False, f"Modalidade ID {id_modalidade} não encontrada.")
        if not novo_nome.strip():
            return RespostaControlador(False, "O nome não pode ser vazio.")
        if novo_preco < 0:
            return RespostaControlador(False, "O preço mensal deve ser maior ou igual a zero.")

        mod.nome_modalidade = novo_nome.strip()
        mod.preco_mensal = novo_preco
        try:
            self.adaptador.atualizar_modalidade(mod)
            return RespostaControlador(True, f"Modalidade ID {id_modalidade} atualizada com sucesso!", mod)
        except Exception as e:
            return RespostaControlador(False, f"Erro ao atualizar modalidade: {e}")

    def excluir_modalidade(self, id_modalidade: int) -> RespostaControlador:
        try:
            sucesso = self.adaptador.excluir_modalidade(id_modalidade)
            if sucesso:
                return RespostaControlador(True, f"Modalidade ID {id_modalidade} excluída com sucesso.")
            return RespostaControlador(False, f"Modalidade ID {id_modalidade} não localizada.")
        except sqlite3.IntegrityError:
            return RespostaControlador(
                False,
                "Restrição de Integridade (ON DELETE RESTRICT): Esta modalidade não pode ser excluída pois possui instrutor(es) vinculado(s)!"
            )
        except Exception as e:
            return RespostaControlador(False, f"Erro ao excluir modalidade: {e}")

    # --- GESTÃO DE ALUNOS ---
    def cadastrar_aluno(self, nome: str, cpf: str, data_matricula: str) -> RespostaControlador:
        nome = nome.strip()
        if not nome:
            return RespostaControlador(False, "O nome do aluno não pode ser vazio.")

        valido, cpf_limpo = self.validar_cpf(cpf)
        if not valido:
            return RespostaControlador(False, cpf_limpo)

        valido_dt, dt_formatada = self.validar_data(data_matricula)
        if not valido_dt:
            return RespostaControlador(False, dt_formatada)

        aluno = Aluno(None, nome, cpf_limpo, dt_formatada)
        try:
            aluno_id = self.adaptador.inserir_aluno(aluno)
            aluno.id_aluno = aluno_id
            return RespostaControlador(True, f"Aluno '{nome}' cadastrado com sucesso! (ID: {aluno_id})", aluno)
        except sqlite3.IntegrityError:
            return RespostaControlador(False, f"Erro: Já existe um aluno cadastrado com o CPF {cpf_limpo} (Restrição UNIQUE violada).")
        except Exception as e:
            return RespostaControlador(False, f"Erro ao cadastrar aluno: {e}")

    def atualizar_aluno(self, id_aluno: int, novo_nome: str, novo_cpf: str, nova_data: str) -> RespostaControlador:
        aluno = self.adaptador.buscar_aluno(id_aluno)
        if not aluno:
            return RespostaControlador(False, f"Aluno ID {id_aluno} não encontrado.")

        valido, cpf_limpo = self.validar_cpf(novo_cpf)
        if not valido:
            return RespostaControlador(False, cpf_limpo)

        valido_dt, dt_formatada = self.validar_data(nova_data)
        if not valido_dt:
            return RespostaControlador(False, dt_formatada)

        aluno.nome_aluno = novo_nome.strip()
        aluno.cpf = cpf_limpo
        aluno.data_matricula = dt_formatada
        try:
            self.adaptador.atualizar_aluno(aluno)
            return RespostaControlador(True, f"Aluno ID {id_aluno} atualizado com sucesso!", aluno)
        except sqlite3.IntegrityError:
            return RespostaControlador(False, "Erro: O CPF informado já pertence a outro aluno cadastrado.")
        except Exception as e:
            return RespostaControlador(False, f"Erro ao atualizar aluno: {e}")

    def excluir_aluno(self, id_aluno: int) -> RespostaControlador:
        """
        Exclui o aluno disparando a regra ON DELETE CASCADE no banco de dados,
        removendo automaticamente as matrículas e o exame médico correspondentes.
        """
        aluno = self.adaptador.buscar_aluno(id_aluno)
        if not aluno:
            return RespostaControlador(False, f"Aluno ID {id_aluno} não encontrado.")

        try:
            self.adaptador.excluir_aluno(id_aluno)
            return RespostaControlador(
                True,
                f"Aluno '{aluno.nome_aluno}' (ID: {id_aluno}) e todos os seus vínculos (matrículas e exame médico) foram excluídos com sucesso via Efeito Cascata (ON DELETE CASCADE)!"
            )
        except Exception as e:
            return RespostaControlador(False, f"Erro ao excluir aluno: {e}")

    # --- GESTÃO DE INSTRUTORES ---
    def cadastrar_instrutor(self, nome: str, cref: str, id_modalidade: int) -> RespostaControlador:
        nome = nome.strip()
        cref = cref.strip().upper()
        if not nome or not cref:
            return RespostaControlador(False, "Nome do instrutor e CREF são campos obrigatórios.")

        mod = self.adaptador.buscar_modalidade(id_modalidade)
        if not mod:
            return RespostaControlador(False, f"Modalidade ID {id_modalidade} informada não existe.")

        instrutor = Instrutor(None, nome, cref, id_modalidade)
        try:
            inst_id = self.adaptador.inserir_instrutor(instrutor)
            instrutor.id_instrutor = inst_id
            return RespostaControlador(True, f"Instrutor '{nome}' cadastrado com sucesso! (ID: {inst_id})", instrutor)
        except sqlite3.IntegrityError:
            return RespostaControlador(False, f"Erro: O CREF '{cref}' já se encontra cadastrado para outro profissional (Restrição UNIQUE violada).")
        except Exception as e:
            return RespostaControlador(False, f"Erro ao cadastrar instrutor: {e}")

    def atualizar_instrutor(self, id_instrutor: int, novo_nome: str, novo_cref: str, nova_id_modalidade: int) -> RespostaControlador:
        instrutor = self.adaptador.buscar_instrutor(id_instrutor)
        if not instrutor:
            return RespostaControlador(False, f"Instrutor ID {id_instrutor} não localizado.")

        novo_nome = novo_nome.strip() or instrutor.nome_instrutor
        novo_cref = novo_cref.strip().upper() or instrutor.cref
        if not self.adaptador.buscar_modalidade(nova_id_modalidade):
            return RespostaControlador(False, f"Modalidade ID {nova_id_modalidade} informada não existe.")

        instrutor.nome_instrutor = novo_nome
        instrutor.cref = novo_cref
        instrutor.id_modalidade = nova_id_modalidade
        try:
            self.adaptador.atualizar_instrutor(instrutor)
            return RespostaControlador(True, f"Instrutor ID {id_instrutor} atualizado com sucesso!", instrutor)
        except sqlite3.IntegrityError:
            return RespostaControlador(False, f"Erro: O CREF '{novo_cref}' já pertence a outro instrutor (Restrição UNIQUE violada).")
        except Exception as e:
            return RespostaControlador(False, f"Erro ao atualizar instrutor: {e}")

    def excluir_instrutor(self, id_instrutor: int) -> RespostaControlador:
        try:
            sucesso = self.adaptador.excluir_instrutor(id_instrutor)
            if sucesso:
                return RespostaControlador(True, f"Instrutor ID {id_instrutor} removido com sucesso.")
            return RespostaControlador(False, f"Instrutor ID {id_instrutor} não localizado.")
        except Exception as e:
            return RespostaControlador(False, f"Erro ao excluir instrutor: {e}")

    # --- GESTÃO DE MATRÍCULAS (N:N) ---
    def matricular_aluno(self, id_aluno: int, id_modalidade: int, data_adesao: Optional[str] = None) -> RespostaControlador:
        aluno = self.adaptador.buscar_aluno(id_aluno)
        if not aluno:
            return RespostaControlador(False, f"Aluno ID {id_aluno} não encontrado.")

        mod = self.adaptador.buscar_modalidade(id_modalidade)
        if not mod:
            return RespostaControlador(False, f"Modalidade ID {id_modalidade} não encontrada.")

        if not data_adesao:
            data_adesao = datetime.date.today().strftime("%Y-%m-%d")
        else:
            valido_dt, data_adesao = self.validar_data(data_adesao)
            if not valido_dt:
                return RespostaControlador(False, data_adesao)

        matricula = MatriculaModalidade(None, data_adesao, id_modalidade, id_aluno)
        try:
            mat_id = self.adaptador.matricular_aluno(matricula)
            matricula.id_matricula_modalidade = mat_id
            return RespostaControlador(
                True,
                f"Matrícula confirmada! Aluno '{aluno.nome_aluno}' vinculado a '{mod.nome_modalidade}' (ID Matrícula: {mat_id}).",
                matricula
            )
        except sqlite3.IntegrityError:
            return RespostaControlador(
                False,
                f"Restrição UNIQUE violada: O aluno '{aluno.nome_aluno}' já está matriculado na modalidade '{mod.nome_modalidade}'!"
            )
        except Exception as e:
            return RespostaControlador(False, f"Erro ao matricular aluno: {e}")

    def cancelar_matricula(self, id_matricula: int) -> RespostaControlador:
        try:
            sucesso = self.adaptador.cancelar_matricula(id_matricula)
            if sucesso:
                return RespostaControlador(True, f"Matrícula ID {id_matricula} cancelada com sucesso.")
            return RespostaControlador(False, f"Matrícula ID {id_matricula} não encontrada.")
        except Exception as e:
            return RespostaControlador(False, f"Erro ao cancelar matrícula: {e}")

    # --- GESTÃO DE EXAMES MÉDICOS (1:1) ---
    def registrar_exame_medico(self, id_aluno: int, situacao: str, data_avaliacao: Optional[str] = None) -> RespostaControlador:
        aluno = self.adaptador.buscar_aluno(id_aluno)
        if not aluno:
            return RespostaControlador(False, f"Aluno ID {id_aluno} não encontrado.")

        situacao = situacao.strip().capitalize()
        if situacao not in ["Apto", "Inapto"]:
            return RespostaControlador(False, "A situação do laudo médico deve ser rigorosamente 'Apto' ou 'Inapto'.")

        if not data_avaliacao:
            data_avaliacao = datetime.date.today().strftime("%Y-%m-%d")
        else:
            valido_dt, data_avaliacao = self.validar_data(data_avaliacao)
            if not valido_dt:
                return RespostaControlador(False, data_avaliacao)

        exame = ExameMedico(None, data_avaliacao, situacao, id_aluno)
        try:
            self.adaptador.inserir_ou_atualizar_exame(exame)
            return RespostaControlador(
                True,
                f"Laudo médico do aluno '{aluno.nome_aluno}' registrado com status '{situacao}' em {data_avaliacao} (Relação 1:1 mantida)."
            )
        except Exception as e:
            return RespostaControlador(False, f"Erro ao registrar exame: {e}")


# ==============================================================================
# CAMADA 1: INTERAÇÃO COM O USUÁRIO (TERMINAL CLI)
# ==============================================================================

class InteracaoUsuario:
    """Interface CLI moderna, rica e amigável para terminal."""

    def __init__(self):
        self.adaptador = AdaptadorMapaObjetoRelacional()
        self.controlador = ControladorCentroEsportivo(self.adaptador)

    # --- MÉTODOS DE FORMATAÇÃO E INTERFACE ---
    @staticmethod
    def limpar_tela():
        os.system("cls" if os.name == "nt" else "clear")

    @staticmethod
    def pausar():
        print(f"\n{Cores.DIM}Pressione ENTER para voltar ao menu...{Cores.RESET}", end="")
        try:
            input()
        except (KeyboardInterrupt, EOFError):
            pass

    @staticmethod
    def exibir_banner():
        banner = f"""
{Cores.CIANO}{Cores.NEGRITO}================================================================================
       SISTEMA DE GESTÃO DO CENTRO ESPORTIVO  ·  BANCO DE DADOS 2 (IFSP)
================================================================================{Cores.RESET}
{Cores.DIM}Arquitetura ORM · Modelagem 1:1, 1:N, N:N · MySQL / SQLite · Turma ADS 2026{Cores.RESET}
"""
        print(banner)

    @staticmethod
    def _tamanho_visivel(texto: Any) -> int:
        """Retorna o comprimento visível de uma string desconsiderando sequências de escape ANSI."""
        s = str(texto) if texto is not None else ""
        return len(re.sub(r'\x1b\[[0-9;]*[mK]', '', s))

    @classmethod
    def exibir_tabela(cls, headers: List[str], rows: List[List[Any]], titulo: Optional[str] = None):
        """Imprime tabelas perfeitamente alinhadas em formato ASCII no terminal."""
        if titulo:
            print(f"\n{Cores.AMARELO}{Cores.NEGRITO}--- [ {titulo} ] ---{Cores.RESET}")

        if not rows:
            print(f"{Cores.DIM}(Nenhum registro encontrado){Cores.RESET}")
            return

        # Calcula largura máxima de cada coluna baseada no texto visível
        col_widths = [cls._tamanho_visivel(h) for h in headers]
        for row in rows:
            for i, val in enumerate(row):
                if i < len(col_widths):
                    col_widths[i] = max(col_widths[i], cls._tamanho_visivel(val))

        # Adiciona padding
        col_widths = [w + 2 for w in col_widths]

        sep_top = "+" + "+".join("-" * w for w in col_widths) + "+"
        header_cells = []
        for h, w in zip(headers, col_widths):
            pad = w - 1 - cls._tamanho_visivel(h)
            header_cells.append(f" {h}{' ' * max(0, pad)}")
        header_row = "|" + "|".join(header_cells) + "|"

        sep_mid = "+" + "+".join("=" * w for w in col_widths) + "+"
        sep_bot = "+" + "+".join("-" * w for w in col_widths) + "+"

        print(f"{Cores.CIANO}{sep_top}")
        print(f"{Cores.CIANO}{header_row}{Cores.RESET}")
        print(f"{Cores.CIANO}{sep_mid}{Cores.RESET}")

        for idx, row in enumerate(rows):
            cor = Cores.BRANCO if idx % 2 == 0 else Cores.DIM
            row_cells = []
            for val, w in zip(row, col_widths):
                val_str = str(val) if val is not None else "-"
                pad = w - 1 - cls._tamanho_visivel(val_str)
                row_cells.append(f" {val_str}{' ' * max(0, pad)}")
            row_str = "|" + "|".join(row_cells) + "|"
            print(f"{cor}{row_str}{Cores.RESET}")

        print(f"{Cores.CIANO}{sep_bot}{Cores.RESET}")
        print(f"{Cores.DIM}Total de registros: {len(rows)}{Cores.RESET}\n")

    # --- MENUS SECUNDÁRIOS ---

    def menu_modalidades(self):
        while True:
            self.limpar_tela()
            self.exibir_banner()
            print(f"{Cores.VERDE}{Cores.NEGRITO}>>> GESTÃO DE MODALIDADES ESPORTIVAS <<<{Cores.RESET}\n")
            print("  [1] Listar todas as modalidades")
            print("  [2] Cadastrar nova modalidade")
            print("  [3] Atualizar preço / nome de modalidade")
            print("  [4] Excluir modalidade (Teste da regra ON DELETE RESTRICT)")
            print("  [0] Voltar ao menu principal")

            opcao = input(f"\n{Cores.AMARELO}Escolha uma opção: {Cores.RESET}").strip()

            if opcao == "1":
                mods = self.adaptador.listar_modalidades()
                rows = [[m.id_modalidade, m.nome_modalidade, f"R$ {m.preco_mensal:.2f}"] for m in mods]
                self.exibir_tabela(["ID", "Modalidade", "Preço Mensal"], rows, "MODALIDADES ATIVAS")
                self.pausar()

            elif opcao == "2":
                print(f"\n{Cores.NEGRITO}--- Novo Cadastro de Modalidade ---{Cores.RESET}")
                nome = input("Nome da modalidade (ex: Natação): ").strip()
                try:
                    preco = float(input("Preço mensal (R$): ").replace(",", "."))
                    resp = self.controlador.cadastrar_modalidade(nome, preco)
                    if resp.sucesso:
                        print(f"\n{Cores.VERDE}✓ {resp.mensagem}{Cores.RESET}")
                    else:
                        print(f"\n{Cores.VERMELHO}✗ {resp.mensagem}{Cores.RESET}")
                except ValueError:
                    print(f"\n{Cores.VERMELHO}✗ Valor de preço inválido.{Cores.RESET}")
                self.pausar()

            elif opcao == "3":
                mods = self.adaptador.listar_modalidades()
                rows = [[m.id_modalidade, m.nome_modalidade, f"R$ {m.preco_mensal:.2f}"] for m in mods]
                self.exibir_tabela(["ID", "Modalidade", "Preço Mensal"], rows, "SELECIONE A MODALIDADE PARA EDITAR")
                try:
                    mod_id = int(input("Informe o ID da modalidade a alterar (ou 0 para cancelar): "))
                    if mod_id != 0:
                        mod = self.adaptador.buscar_modalidade(mod_id)
                        if not mod:
                            print(f"{Cores.VERMELHO}✗ Modalidade não encontrada.{Cores.RESET}")
                        else:
                            novo_nome = input(f"Novo nome [{mod.nome_modalidade}]: ").strip() or mod.nome_modalidade
                            preco_str = input(f"Novo preço mensal [{mod.preco_mensal:.2f}]: ").strip()
                            novo_preco = float(preco_str.replace(",", ".")) if preco_str else mod.preco_mensal
                            resp = self.controlador.atualizar_modalidade(mod_id, novo_nome, novo_preco)
                            if resp.sucesso:
                                print(f"\n{Cores.VERDE}✓ {resp.mensagem}{Cores.RESET}")
                            else:
                                print(f"\n{Cores.VERMELHO}✗ {resp.mensagem}{Cores.RESET}")
                except ValueError:
                    print(f"\n{Cores.VERMELHO}✗ Entrada numérica inválida.{Cores.RESET}")
                self.pausar()

            elif opcao == "4":
                mods = self.adaptador.listar_modalidades()
                rows = [[m.id_modalidade, m.nome_modalidade, f"R$ {m.preco_mensal:.2f}"] for m in mods]
                self.exibir_tabela(["ID", "Modalidade", "Preço Mensal"], rows, "EXCLUSÃO DE MODALIDADE")
                print(f"{Cores.AMARELO}Nota de Aula: Modalidades com instrutor vinculado acionam RESTRICT e não são apagadas.{Cores.RESET}")
                try:
                    mod_id = int(input("Informe o ID da modalidade a excluir (ou 0 para cancelar): "))
                    if mod_id != 0:
                        resp = self.controlador.excluir_modalidade(mod_id)
                        if resp.sucesso:
                            print(f"\n{Cores.VERDE}✓ {resp.mensagem}{Cores.RESET}")
                        else:
                            print(f"\n{Cores.VERMELHO}✗ {resp.mensagem}{Cores.RESET}")
                except ValueError:
                    print(f"\n{Cores.VERMELHO}✗ Entrada inválida.{Cores.RESET}")
                self.pausar()

            elif opcao == "0":
                break

    def menu_instrutores(self):
        while True:
            self.limpar_tela()
            self.exibir_banner()
            print(f"{Cores.VERDE}{Cores.NEGRITO}>>> GESTÃO DE INSTRUTORES (RELAÇÃO 1:N) <<<{Cores.RESET}\n")
            print("  [1] Listar todos os instrutores e suas modalidades")
            print("  [2] Cadastrar novo instrutor")
            print("  [3] Excluir instrutor")
            print("  [4] Atualizar instrutor")
            print("  [0] Voltar ao menu principal")

            opcao = input(f"\n{Cores.AMARELO}Escolha uma opção: {Cores.RESET}").strip()

            if opcao == "1":
                insts = self.adaptador.listar_instrutores()
                rows = [[i["id_instrutor"], i["nome_instrutor"], i["cref"], f"{i['nome_modalidade']} (ID {i['id_modalidade']})"] for i in insts]
                self.exibir_tabela(["ID", "Nome do Instrutor", "CREF", "Modalidade Lecionada"], rows, "CORPO DOCENTE / INSTRUTORES")
                self.pausar()

            elif opcao == "2":
                print(f"\n{Cores.NEGRITO}--- Novo Cadastro de Instrutor ---{Cores.RESET}")
                nome = input("Nome completo: ").strip()
                cref = input("Número de registro CREF (ex: CREF/SP 66666): ").strip()

                mods = self.adaptador.listar_modalidades()
                rows = [[m.id_modalidade, m.nome_modalidade] for m in mods]
                self.exibir_tabela(["ID", "Modalidade"], rows, "SELECIONE A MODALIDADE VINCULADA")

                try:
                    id_mod = int(input("Informe o ID da modalidade: "))
                    resp = self.controlador.cadastrar_instrutor(nome, cref, id_mod)
                    if resp.sucesso:
                        print(f"\n{Cores.VERDE}✓ {resp.mensagem}{Cores.RESET}")
                    else:
                        print(f"\n{Cores.VERMELHO}✗ {resp.mensagem}{Cores.RESET}")
                except ValueError:
                    print(f"\n{Cores.VERMELHO}✗ ID inválido.{Cores.RESET}")
                self.pausar()

            elif opcao == "3":
                insts = self.adaptador.listar_instrutores()
                rows = [[i["id_instrutor"], i["nome_instrutor"], i["cref"], i["nome_modalidade"]] for i in insts]
                self.exibir_tabela(["ID", "Nome", "CREF", "Modalidade"], rows, "REMOVER INSTRUTOR")
                try:
                    id_inst = int(input("Informe o ID do instrutor a remover (ou 0 para cancelar): "))
                    if id_inst != 0:
                        resp = self.controlador.excluir_instrutor(id_inst)
                        if resp.sucesso:
                            print(f"\n{Cores.VERDE}✓ {resp.mensagem}{Cores.RESET}")
                        else:
                            print(f"\n{Cores.VERMELHO}✗ {resp.mensagem}{Cores.RESET}")
                except ValueError:
                    print(f"\n{Cores.VERMELHO}✗ Entrada numérica inválida.{Cores.RESET}")
                self.pausar()

            elif opcao == "4":
                insts = self.adaptador.listar_instrutores()
                rows = [[i["id_instrutor"], i["nome_instrutor"], i["cref"], f"{i['nome_modalidade']} (ID {i['id_modalidade']})"] for i in insts]
                self.exibir_tabela(["ID", "Nome", "CREF", "Modalidade"], rows, "ATUALIZAR INSTRUTOR")
                try:
                    id_inst = int(input("Informe o ID do instrutor a atualizar (ou 0 para cancelar): "))
                    if id_inst != 0:
                        atual = self.adaptador.buscar_instrutor(id_inst)
                        if not atual:
                            print(f"\n{Cores.VERMELHO}✗ Instrutor ID {id_inst} não localizado.{Cores.RESET}")
                        else:
                            print(f"{Cores.CIANO}(Deixe em branco para manter o valor atual){Cores.RESET}")
                            nome = input(f"Nome [{atual.nome_instrutor}]: ")
                            cref = input(f"CREF [{atual.cref}]: ")
                            mods = self.adaptador.listar_modalidades()
                            self.exibir_tabela(["ID", "Modalidade"], [[m.id_modalidade, m.nome_modalidade] for m in mods], "MODALIDADES")
                            mod_txt = input(f"ID da modalidade [{atual.id_modalidade}]: ").strip()
                            id_mod = int(mod_txt) if mod_txt else atual.id_modalidade
                            resp = self.controlador.atualizar_instrutor(id_inst, nome, cref, id_mod)
                            if resp.sucesso:
                                print(f"\n{Cores.VERDE}✓ {resp.mensagem}{Cores.RESET}")
                            else:
                                print(f"\n{Cores.VERMELHO}✗ {resp.mensagem}{Cores.RESET}")
                except ValueError:
                    print(f"\n{Cores.VERMELHO}✗ Entrada numérica inválida.{Cores.RESET}")
                self.pausar()

            elif opcao == "0":
                break

    def menu_alunos(self):
        while True:
            self.limpar_tela()
            self.exibir_banner()
            print(f"{Cores.VERDE}{Cores.NEGRITO}>>> GESTÃO DE ALUNOS <<<{Cores.RESET}\n")
            print("  [1] Listar todos os alunos")
            print("  [2] Cadastrar novo aluno")
            print("  [3] Atualizar dados de aluno (Nome / CPF / Data)")
            print("  [4] Excluir aluno (Teste do efeito em cascata ON DELETE CASCADE)")
            print("  [0] Voltar ao menu principal")

            opcao = input(f"\n{Cores.AMARELO}Escolha uma opção: {Cores.RESET}").strip()

            if opcao == "1":
                alunos = self.adaptador.listar_alunos()
                rows = [[a.id_aluno, a.nome_aluno, a.cpf_formatado(), a.data_matricula] for a in alunos]
                self.exibir_tabela(["ID", "Nome do Aluno", "CPF", "Data de Matrícula"], rows, "ALUNOS CADASTRADOS")
                self.pausar()

            elif opcao == "2":
                print(f"\n{Cores.NEGRITO}--- Novo Cadastro de Aluno ---{Cores.RESET}")
                nome = input("Nome completo do aluno: ").strip()
                cpf = input("CPF (11 dígitos, ex: 12345678901): ").strip()
                data_mat = input(f"Data de matrícula [Padrão hoje: {datetime.date.today().strftime('%Y-%m-%d')}]: ").strip()
                if not data_mat:
                    data_mat = datetime.date.today().strftime("%Y-%m-%d")

                resp = self.controlador.cadastrar_aluno(nome, cpf, data_mat)
                if resp.sucesso:
                    print(f"\n{Cores.VERDE}✓ {resp.mensagem}{Cores.RESET}")
                else:
                    print(f"\n{Cores.VERMELHO}✗ {resp.mensagem}{Cores.RESET}")
                self.pausar()

            elif opcao == "3":
                alunos = self.adaptador.listar_alunos()
                rows = [[a.id_aluno, a.nome_aluno, a.cpf_formatado(), a.data_matricula] for a in alunos]
                self.exibir_tabela(["ID", "Nome", "CPF", "Data Matrícula"], rows, "SELECIONE O ALUNO PARA EDITAR")
                try:
                    aluno_id = int(input("Informe o ID do aluno a alterar (ou 0 para cancelar): "))
                    if aluno_id != 0:
                        aluno = self.adaptador.buscar_aluno(aluno_id)
                        if not aluno:
                            print(f"{Cores.VERMELHO}✗ Aluno não encontrado.{Cores.RESET}")
                        else:
                            novo_nome = input(f"Novo nome [{aluno.nome_aluno}]: ").strip() or aluno.nome_aluno
                            novo_cpf = input(f"Novo CPF [{aluno.cpf}]: ").strip() or aluno.cpf
                            nova_data = input(f"Nova data matrícula [{aluno.data_matricula}]: ").strip() or aluno.data_matricula

                            resp = self.controlador.atualizar_aluno(aluno_id, novo_nome, novo_cpf, nova_data)
                            if resp.sucesso:
                                print(f"\n{Cores.VERDE}✓ {resp.mensagem}{Cores.RESET}")
                            else:
                                print(f"\n{Cores.VERMELHO}✗ {resp.mensagem}{Cores.RESET}")
                except ValueError:
                    print(f"\n{Cores.VERMELHO}✗ Entrada numérica inválida.{Cores.RESET}")
                self.pausar()

            elif opcao == "4":
                alunos = self.adaptador.listar_alunos()
                rows = [[a.id_aluno, a.nome_aluno, a.cpf_formatado(), a.data_matricula] for a in alunos]
                self.exibir_tabela(["ID", "Nome", "CPF", "Data Matrícula"], rows, "EXCLUSÃO DE ALUNO COM EFEITO CASCADE")
                print(f"{Cores.AMARELO}Nota de Aula (Slide 16): Ao apagar o aluno, suas matrículas e laudo médico são deletados automaticamente!{Cores.RESET}")
                try:
                    aluno_id = int(input("Informe o ID do aluno a excluir (ou 0 para cancelar): "))
                    if aluno_id != 0:
                        resp = self.controlador.excluir_aluno(aluno_id)
                        if resp.sucesso:
                            print(f"\n{Cores.VERDE}✓ {resp.mensagem}{Cores.RESET}")
                        else:
                            print(f"\n{Cores.VERMELHO}✗ {resp.mensagem}{Cores.RESET}")
                except ValueError:
                    print(f"\n{Cores.VERMELHO}✗ Entrada numérica inválida.{Cores.RESET}")
                self.pausar()

            elif opcao == "0":
                break

    def menu_matriculas(self):
        while True:
            self.limpar_tela()
            self.exibir_banner()
            print(f"{Cores.VERDE}{Cores.NEGRITO}>>> GESTÃO DE MATRÍCULAS (RELAÇÃO N:N) <<<{Cores.RESET}\n")
            print("  [1] Listar todas as matrículas ativas")
            print("  [2] Matricular aluno em modalidade esportiva")
            print("  [3] Cancelar matrícula")
            print("  [0] Voltar ao menu principal")

            opcao = input(f"\n{Cores.AMARELO}Escolha uma opção: {Cores.RESET}").strip()

            if opcao == "1":
                mats = self.adaptador.listar_matriculas()
                rows = [[
                    m["id_matricula_modalidade"],
                    f"{m['nome_aluno']} (ID {m['id_aluno']})",
                    f"{m['nome_modalidade']} (ID {m['id_modalidade']})",
                    f"R$ {m['preco_mensal']:.2f}",
                    m["data_adesao"]
                ] for m in mats]
                self.exibir_tabela(["ID Matrícula", "Aluno", "Modalidade Cursada", "Mensalidade", "Data de Adesão"], rows, "MATRÍCULAS ATIVAS")
                self.pausar()

            elif opcao == "2":
                print(f"\n{Cores.NEGRITO}--- Nova Matrícula ---{Cores.RESET}")
                alunos = self.adaptador.listar_alunos()
                self.exibir_tabela(["ID", "Nome do Aluno", "CPF"], [[a.id_aluno, a.nome_aluno, a.cpf_formatado()] for a in alunos], "ALUNOS")

                try:
                    id_aluno = int(input("Informe o ID do aluno: "))
                    mods = self.adaptador.listar_modalidades()
                    self.exibir_tabela(["ID", "Modalidade", "Preço"], [[m.id_modalidade, m.nome_modalidade, f"R$ {m.preco_mensal:.2f}"] for m in mods], "MODALIDADES")

                    id_mod = int(input("Informe o ID da modalidade a aderir: "))
                    dt = input(f"Data de adesão [Padrão hoje: {datetime.date.today().strftime('%Y-%m-%d')}]: ").strip()
                    resp = self.controlador.matricular_aluno(id_aluno, id_mod, dt or None)

                    if resp.sucesso:
                        print(f"\n{Cores.VERDE}✓ {resp.mensagem}{Cores.RESET}")
                    else:
                        print(f"\n{Cores.VERMELHO}✗ {resp.mensagem}{Cores.RESET}")
                except ValueError:
                    print(f"\n{Cores.VERMELHO}✗ ID numérico inválido.{Cores.RESET}")
                self.pausar()

            elif opcao == "3":
                mats = self.adaptador.listar_matriculas()
                rows = [[
                    m["id_matricula_modalidade"],
                    m["nome_aluno"],
                    m["nome_modalidade"],
                    m["data_adesao"]
                ] for m in mats]
                self.exibir_tabela(["ID Matrícula", "Aluno", "Modalidade", "Data Adesão"], rows, "CANCELAMENTO DE MATRÍCULA")
                try:
                    id_mat = int(input("Informe o ID da matrícula a cancelar (ou 0 para desistir): "))
                    if id_mat != 0:
                        resp = self.controlador.cancelar_matricula(id_mat)
                        if resp.sucesso:
                            print(f"\n{Cores.VERDE}✓ {resp.mensagem}{Cores.RESET}")
                        else:
                            print(f"\n{Cores.VERMELHO}✗ {resp.mensagem}{Cores.RESET}")
                except ValueError:
                    print(f"\n{Cores.VERMELHO}✗ Entrada inválida.{Cores.RESET}")
                self.pausar()

            elif opcao == "0":
                break

    def menu_exames(self):
        while True:
            self.limpar_tela()
            self.exibir_banner()
            print(f"{Cores.VERDE}{Cores.NEGRITO}>>> GESTÃO DE EXAMES MÉDICOS (RELAÇÃO 1:1) <<<{Cores.RESET}\n")
            print("  [1] Listar todos os exames médicos cadastrados")
            print("  [2] Lançar ou atualizar laudo médico de aluno (Apto / Inapto)")
            print("  [3] Excluir exame médico")
            print("  [0] Voltar ao menu principal")

            opcao = input(f"\n{Cores.AMARELO}Escolha uma opção: {Cores.RESET}").strip()

            if opcao == "1":
                exames = self.adaptador.listar_exames()
                rows = []
                for e in exames:
                    status_cor = f"{Cores.VERDE}Apto{Cores.RESET}" if e["situacao"] == "Apto" else f"{Cores.VERMELHO}Inapto{Cores.RESET}"
                    rows.append([
                        e["id_exame"],
                        f"{e['nome_aluno']} (ID {e['id_aluno']})",
                        status_cor,
                        e["data_avaliacao"]
                    ])
                self.exibir_tabela(["ID Exame", "Aluno", "Status Clínico", "Data da Avaliação"], rows, "AVALIAÇÕES MÉDICAS")
                self.pausar()

            elif opcao == "2":
                print(f"\n{Cores.NEGRITO}--- Lançamento de Laudo Médico ---{Cores.RESET}")
                alunos = self.adaptador.listar_alunos()
                self.exibir_tabela(["ID", "Nome do Aluno", "CPF"], [[a.id_aluno, a.nome_aluno, a.cpf_formatado()] for a in alunos], "ALUNOS")

                try:
                    id_aluno = int(input("Informe o ID do aluno examinado: "))
                    situacao = input("Situação médica [Apto / Inapto]: ").strip()
                    dt = input(f"Data da avaliação [Padrão hoje: {datetime.date.today().strftime('%Y-%m-%d')}]: ").strip()

                    resp = self.controlador.registrar_exame_medico(id_aluno, situacao, dt or None)
                    if resp.sucesso:
                        print(f"\n{Cores.VERDE}✓ {resp.mensagem}{Cores.RESET}")
                    else:
                        print(f"\n{Cores.VERMELHO}✗ {resp.mensagem}{Cores.RESET}")
                except ValueError:
                    print(f"\n{Cores.VERMELHO}✗ Entrada inválida.{Cores.RESET}")
                self.pausar()

            elif opcao == "3":
                exames = self.adaptador.listar_exames()
                rows = [[e["id_exame"], e["nome_aluno"], e["situacao"], e["data_avaliacao"]] for e in exames]
                self.exibir_tabela(["ID Exame", "Aluno", "Situação", "Data"], rows, "REMOVER EXAME MÉDICO")
                try:
                    id_exame = int(input("Informe o ID do exame a remover (ou 0 para cancelar): "))
                    if id_exame != 0:
                        if self.adaptador.excluir_exame(id_exame):
                            print(f"\n{Cores.VERDE}✓ Exame ID {id_exame} removido com sucesso.{Cores.RESET}")
                        else:
                            print(f"\n{Cores.VERMELHO}✗ Exame não localizado.{Cores.RESET}")
                except ValueError:
                    print(f"\n{Cores.VERMELHO}✗ Entrada numérica inválida.{Cores.RESET}")
                self.pausar()

            elif opcao == "0":
                break

    # --- MENU DE CONSULTAS COMPLEXAS DO TRABALHO ---

    def menu_consultas_complexas(self):
        while True:
            self.limpar_tela()
            self.exibir_banner()
            print(f"{Cores.MAGENTA}{Cores.NEGRITO}>>> RELATÓRIOS & SELEÇÕES COMPLEXAS (BANCO DE DADOS 2) <<<{Cores.RESET}\n")
            print("  [1] Consulta 1: Ficha Geral de Alunos com Exame Apto (Junção de 5 tabelas)")
            print("  [2] Consulta 2: Auditoria Médica Preventiva (Alunos Inaptos em Atividades)")
            print("  [3] Consulta 3: Faturamento Estimado e Quantidade de Alunos por Modalidade")
            print("  [4] Consulta 4: Alunos Multidisciplinares e Mensalidade Acumulada")
            print("  [5] Executar Todas as 4 Consultas Sequencialmente")
            print("  [0] Voltar ao menu principal")

            opcao = input(f"\n{Cores.AMARELO}Escolha uma consulta para executar: {Cores.RESET}").strip()

            if opcao == "1":
                self.executar_consulta_1()
                self.pausar()

            elif opcao == "2":
                self.executar_consulta_2()
                self.pausar()

            elif opcao == "3":
                self.executar_consulta_3()
                self.pausar()

            elif opcao == "4":
                self.executar_consulta_4()
                self.pausar()

            elif opcao == "5":
                self.executar_consulta_1()
                self.executar_consulta_2()
                self.executar_consulta_3()
                self.executar_consulta_4()
                self.pausar()

            elif opcao == "0":
                break

    def executar_consulta_1(self):
        print(f"\n{Cores.CIANO}{Cores.NEGRITO}================================================================================")
        print("CONSULTA 1: FICHA GERAL DE ALUNOS COM EXAME APTO (JUNÇÃO DE 5 TABELAS)")
        print(f"================================================================================{Cores.RESET}")
        print(f"{Cores.DIM}Objetivo: Cruzar Alunos, Matrículas, Modalidades, Instrutores e Exames Médicos.")
        print(f"Filtros: situacao = 'Apto' AND preco_mensal >= R$ 90.00{Cores.RESET}\n")

        resultados = self.adaptador.consulta_1_alunos_aptos(90.0)
        headers = ["Aluno", "CPF", "Modalidade", "Mensalidade", "Instrutor Responsável", "CREF", "Situação", "Data Adesão"]
        rows = [[
            r["Aluno"],
            r["CPF"],
            r["Modalidade"],
            r["Mensalidade"],
            r["Instrutor_Responsavel"],
            r["CREF"],
            f"{Cores.VERDE}{r['Situacao_Medica']}{Cores.RESET}",
            r["Data_Adesao"]
        ] for r in resultados]
        self.exibir_tabela(headers, rows)

    def executar_consulta_2(self):
        print(f"\n{Cores.CIANO}{Cores.NEGRITO}================================================================================")
        print("CONSULTA 2: AUDITORIA MÉDICA PREVENTIVA (ALUNOS INAPTOS EM ATIVIDADES)")
        print(f"================================================================================{Cores.RESET}")
        print(f"{Cores.DIM}Objetivo: Detectar alunos matriculados sem laudo médico apto para bloqueio na catraca.")
        print(f"Filtros: situacao = 'Inapto'{Cores.RESET}\n")

        resultados = self.adaptador.consulta_2_auditoria_medica_inaptos()
        headers = ["ID Aluno", "Aluno", "Status Exame", "Data Avaliação", "Modalidade Matriculada", "Instrutor Avisado"]
        rows = [[
            r["id_aluno"],
            r["Aluno"],
            f"{Cores.VERMELHO}{r['Status_Exame']}{Cores.RESET}",
            r["Data_Avaliacao_Medica"],
            r["Modalidade_Matriculada"],
            r["Instrutor_Avisado"]
        ] for r in resultados]
        self.exibir_tabela(headers, rows)

    def executar_consulta_3(self):
        print(f"\n{Cores.CIANO}{Cores.NEGRITO}================================================================================")
        print("CONSULTA 3: FATURAMENTO ESTIMADO E QUANTIDADE DE ALUNOS POR MODALIDADE")
        print(f"================================================================================{Cores.RESET}")
        print(f"{Cores.DIM}Objetivo: Apurar faturamento com LEFT JOIN, GROUP BY, COUNT, SUM e HAVING.")
        print(f"Filtros: HAVING COUNT(mm.id_aluno) > 0  (Ordenado por receita gerada DESC){Cores.RESET}\n")

        resultados = self.adaptador.consulta_3_faturamento_por_modalidade()
        headers = ["ID", "Modalidade", "Instrutor", "Valor Unitário", "Total Alunos", "Receita Mensal Gerada"]
        rows = [[
            r["id_modalidade"],
            r["Modalidade"],
            r["Instrutor"],
            r["Valor_Unitario"],
            r["Total_Alunos_Matriculados"],
            f"{Cores.VERDE}{r['Receita_Mensal_Gerada']}{Cores.RESET}"
        ] for r in resultados]
        self.exibir_tabela(headers, rows)

    def executar_consulta_4(self):
        print(f"\n{Cores.CIANO}{Cores.NEGRITO}================================================================================")
        print("CONSULTA 4: ALUNOS MULTIDISCIPLINARES E MENSALIDADE ACUMULADA")
        print(f"================================================================================{Cores.RESET}")
        print(f"{Cores.DIM}Objetivo: Localizar quem pratica mais de 1 esporte com GROUP BY, HAVING > 1,")
        print(f"          GROUP_CONCAT e cálculo do pacote financeiro total.{Cores.RESET}\n")

        resultados = self.adaptador.consulta_4_alunos_multidisciplinares()
        headers = ["ID Aluno", "Aluno", "Qtd Esportes", "Modalidades Cursadas", "Mensalidade Total do Aluno"]
        rows = [[
            r["id_aluno"],
            r["Aluno"],
            r["Qtd_Modalidades"],
            r["Modalidades_Cursadas"],
            f"{Cores.VERDE}{r['Mensalidade_Total_Aluno']}{Cores.RESET}"
        ] for r in resultados]
        self.exibir_tabela(headers, rows)

    # --- MENU DE LABORATÓRIO E TESTES DOS SLIDES ---

    def menu_laboratorio_testes(self):
        while True:
            self.limpar_tela()
            self.exibir_banner()
            print(f"{Cores.AMARELO}{Cores.NEGRITO}>>> LABORATÓRIO DE TESTES E DEMONSTRAÇÕES DOS SLIDES <<<{Cores.RESET}\n")
            print("  [1] Executar os 3 UPDATEs do Slide 15")
            print("      - Reajuste de 10% nas modalidades > R$ 100,00")
            print("      - Liberação médica do aluno Jeremias Souza (Inapto -> Apto)")
            print("      - Atualização cadastral de Helena Vieira por CPF")
            print()
            print("  [2] Executar as 2 Remoções do Slide 16 e Auditar o CASCADE")
            print("      - Cancelamento da matrícula de Jeremias em Natação")
            print("      - Exclusão da aluna Camila Ribeiro (id 2) e auditoria de órfãos")
            print()
            print("  [3] Restaurar / Resetar Banco para o Estado Inicial (27 Registros)")
            print("  [0] Voltar ao menu principal")

            opcao = input(f"\n{Cores.AMARELO}Escolha uma opção de laboratório: {Cores.RESET}").strip()

            if opcao == "1":
                print(f"\n{Cores.CIANO}Executando os 3 UPDATEs do Slide 15...{Cores.RESET}")
                res = self.adaptador.executar_updates_slide_15()
                print(f"{Cores.VERDE}✓ Modalidades reajustadas (+10%): {res['modalidades_reajustadas']}{Cores.RESET}")
                print(f"{Cores.VERDE}✓ Exame de Jeremias liberado para Apto: {res['exames_liberados']}{Cores.RESET}")
                print(f"{Cores.VERDE}✓ Cadastro de Helena atualizado por CPF: {res['alunos_atualizados']}{Cores.RESET}")

                print(f"\n{Cores.AMARELO}Novos Preços das Modalidades:{Cores.RESET}")
                mods = self.adaptador.listar_modalidades()
                self.exibir_tabela(["ID", "Modalidade", "Preço Atualizado"], [[m.id_modalidade, m.nome_modalidade, f"R$ {m.preco_mensal:.2f}"] for m in mods])
                self.pausar()

            elif opcao == "2":
                print(f"\n{Cores.CIANO}Executando os 2 DELETEs do Slide 16 com auditoria de integridade...{Cores.RESET}")
                res = self.adaptador.executar_deletes_slide_16()
                print(f"{Cores.VERDE}✓ Matrícula de Jeremias cancelada: {res['matriculas_canceladas']}{Cores.RESET}")
                print(f"{Cores.VERDE}✓ Aluna Camila Ribeiro excluída: {res['alunas_removidas']}{Cores.RESET}")
                print(f"{Cores.VERDE}✓ Auditoria em Cascata - Matrículas órfãs da aluna 2: {res['orfaos_matriculas']} (Sucesso){Cores.RESET}")
                print(f"{Cores.VERDE}✓ Auditoria em Cascata - Exames órfãos da aluna 2: {res['orfaos_exames']} (Sucesso){Cores.RESET}")
                self.pausar()

            elif opcao == "3":
                confirmacao = input("Deseja realmente resetar e restaurar a base oficial de 27 registros? (S/N): ").strip().upper()
                if confirmacao == "S":
                    self.adaptador.resetar_banco()
                    print(f"\n{Cores.VERDE}✓ Banco restaurado com sucesso! 27 registros carregados.{Cores.RESET}")
                else:
                    print("\nOperação cancelada.")
                self.pausar()

            elif opcao == "0":
                break

    # --- INFORMAÇÕES E SCRIPT SQL ---

    def exibir_script_sql(self):
        self.limpar_tela()
        self.exibir_banner()
        print(f"{Cores.CIANO}{Cores.NEGRITO}>>> SCRIPT SQL DO CENTRO ESPORTIVO (MySQL 8) <<<{Cores.RESET}\n")
        sql_path = os.path.join(os.path.dirname(__file__), "centro_esportivo.sql")
        if os.path.exists(sql_path):
            print(f"{Cores.DIM}Arquivo localizado em: {sql_path}{Cores.RESET}\n")
            with open(sql_path, "r", encoding="utf-8") as f:
                linhas = f.readlines()
            for l in linhas[:60]:
                print(l, end="")
            if len(linhas) > 60:
                print(f"\n{Cores.AMARELO}... [Exibindo primeiras 60 linhas de {len(linhas)}. O script completo está salvo no diretório]{Cores.RESET}")
        else:
            print(f"{Cores.VERMELHO}Arquivo centro_esportivo.sql não encontrado.{Cores.RESET}")
        self.pausar()

    def exibir_arquitetura(self):
        self.limpar_tela()
        self.exibir_banner()
        print(f"{Cores.CIANO}{Cores.NEGRITO}>>> ARQUITETURA DE PERSISTÊNCIA E DIAGRAMA DE CLASSES <<<{Cores.RESET}\n")
        info = f"""
{Cores.NEGRITO}1. Fluxo em Camadas Adotado:{Cores.RESET}
   [InteracaoUsuario] (Terminal CLI)
          │
          ▼
     [Controlador] (Regras de Negócio e Validações)
          │
          ├──> Manipula Objetos: Modalidade, Aluno, Instrutor, MatriculaModalidade, ExameMedico
          │
          ▼
   [AdaptadorMapaObjetoRelacional] (ORM)
          │  - Serializa/Desserializa objetos eliminando a incompatibilidade de impedância
          ▼
    [SGBD Relacional] (SQLite integrado com chaves estrangeiras ativas / MySQL 8)

{Cores.NEGRITO}2. Relações do Modelo de Dados:{Cores.RESET}
   - {Cores.VERDE}1:N (Modalidades -> Instrutores):{Cores.RESET}
     1 modalidade reúne N instrutores. ON DELETE RESTRICT impede exclusão de modalidade em uso.
   - {Cores.VERDE}N:N (Alunos <-> Modalidades):{Cores.RESET}
     Tabela associativa MatriculasModalidades com data de adesão e UNIQUE(id_aluno, id_modalidade).
   - {Cores.VERDE}1:1 (Alunos -> ExamesMedicos):{Cores.RESET}
     Tabela ExamesMedicos com id_aluno UNIQUE e ON DELETE CASCADE.

{Cores.NEGRITO}3. Restrições e Tipos Validados:{Cores.RESET}
   - AUTO_INCREMENT (ou AUTOINCREMENT) em todas as chaves primárias.
   - CPF único de 11 dígitos em Alunos.
   - CREF único por Instrutor.
   - CHECK (preco_mensal >= 0) e CHECK (situacao IN ('Apto', 'Inapto')).
"""
        print(info)
        self.pausar()

    # --- LOOP PRINCIPAL DO PROGRAMA ---

    def executar(self):
        while True:
            self.limpar_tela()
            self.exibir_banner()
            print(f"{Cores.NEGRITO}MENU PRINCIPAL:{Cores.RESET}\n")
            print(f"  {Cores.CIANO}[1]{Cores.RESET} Gestão de Modalidades Esportivas")
            print(f"  {Cores.CIANO}[2]{Cores.RESET} Gestão de Instrutores (Relação 1:N)")
            print(f"  {Cores.CIANO}[3]{Cores.RESET} Gestão de Alunos (Cadastro e Exclusão com CASCADE)")
            print(f"  {Cores.CIANO}[4]{Cores.RESET} Gestão de Matrículas (Relação N:N Associativa)")
            print(f"  {Cores.CIANO}[5]{Cores.RESET} Gestão de Exames Médicos (Relação 1:1)")
            print(f"  {Cores.MAGENTA}[6]{Cores.RESET} {Cores.NEGRITO}Relatórios e Seleções Complexas (As 4 Consultas de BD2){Cores.RESET}")
            print(f"  {Cores.AMARELO}[7]{Cores.RESET} Laboratório de Testes dos Slides (Slide 15 e 16 / Reset)")
            print(f"  {Cores.BRANCO}[8]{Cores.RESET} Visualizar Script SQL Completo (centro_esportivo.sql)")
            print(f"  {Cores.BRANCO}[9]{Cores.RESET} Detalhes da Arquitetura e Diagramas")
            print(f"  {Cores.VERMELHO}[0]{Cores.RESET} Sair do Sistema")

            try:
                escolha = input(f"\n{Cores.AMARELO}Selecione a opção desejada: {Cores.RESET}").strip()
            except (KeyboardInterrupt, EOFError):
                print(f"\n\n{Cores.CIANO}Encerrando aplicação. Até logo!{Cores.RESET}\n")
                break

            if escolha == "1":
                self.menu_modalidades()
            elif escolha == "2":
                self.menu_instrutores()
            elif escolha == "3":
                self.menu_alunos()
            elif escolha == "4":
                self.menu_matriculas()
            elif escolha == "5":
                self.menu_exames()
            elif escolha == "6":
                self.menu_consultas_complexas()
            elif escolha == "7":
                self.menu_laboratorio_testes()
            elif escolha == "8":
                self.exibir_script_sql()
            elif escolha == "9":
                self.exibir_arquitetura()
            elif escolha == "0":
                print(f"\n{Cores.VERDE}Sistema encerrado com sucesso. Bons estudos!{Cores.RESET}\n")
                break
            else:
                print(f"{Cores.VERMELHO}Opção inválida. Tente novamente.{Cores.RESET}")
                self.pausar()


# ==============================================================================
# PONTO DE ENTRADA
# ==============================================================================

if __name__ == "__main__":
    app = InteracaoUsuario()
    app.executar()
