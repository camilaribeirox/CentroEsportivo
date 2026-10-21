import os
import shutil
import sqlite3
import subprocess
from datetime import date
import questionary
from questionary import Choice

try:
    import pymysql
except ImportError:
    pymysql = None

try:
    import mysql.connector as mysql_connector
except ImportError:
    mysql_connector = None


class Modalidade:
    def __init__(self, idModalidade, nome, precoMensal):
        self.idModalidade = int(idModalidade) if idModalidade is not None else None
        self.nome = nome
        self.precoMensal = float(precoMensal)


class Instrutor:
    def __init__(self, idInstrutor, nome, cref, idModalidade):
        self.idInstrutor = int(idInstrutor) if idInstrutor is not None else None
        self.nome = nome
        self.cref = cref
        self.idModalidade = int(idModalidade)


def validar_data(valor):
    """Garante o formato AAAA-MM-DD (também no modo SQLite, que não valida datas)."""
    texto = str(valor).strip()
    try:
        date.fromisoformat(texto)
    except ValueError:
        raise ValueError(f"Data inválida: '{texto}'. Use o formato AAAA-MM-DD.")
    return texto


class Aluno:
    def __init__(self, idAluno, nome, cpf, dataMatricula):
        self.idAluno = int(idAluno) if idAluno is not None else None
        self.nome = nome
        self.cpf = cpf
        self.dataMatricula = validar_data(dataMatricula)


class MatriculaModalidade:
    def __init__(self, idMatriculaModalidade, dataAdesao, idModalidade, idAluno):
        self.idMatriculaModalidade = int(idMatriculaModalidade) if idMatriculaModalidade is not None else None
        self.dataAdesao = validar_data(dataAdesao)
        self.idModalidade = int(idModalidade)
        self.idAluno = int(idAluno)


class ExameMedico:
    def __init__(self, idExame, dataAvaliacao, situacao, idAluno):
        self.idExame = int(idExame) if idExame is not None else None
        self.dataAvaliacao = validar_data(dataAvaliacao)
        self.situacao = situacao
        self.idAluno = int(idAluno)


class AdaptadorMapaObjetoRelacional:
    def __init__(self, host="localhost", user="root", password=None, database="centro_esportivo"):
        self.host = host
        self.user = user
        self.password = password
        self.database = database
        self.modo = None
        self.mysql_bin = self._localizar_mysql_cli()
        self.sqlite_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "centro_esportivo.db")
        self._configurar_conexao()

    def _localizar_mysql_cli(self):
        no_path = shutil.which("mysql")
        if no_path:
            return no_path
        caminhos_comuns = [
            r"C:\Program Files\MySQL\MySQL Server 8.0\bin\mysql.exe",
            r"C:\Program Files\MySQL\MySQL Server 8.4\bin\mysql.exe",
            r"C:\xampp\mysql\bin\mysql.exe",
        ]
        for c in caminhos_comuns:
            if os.path.exists(c):
                return c
        return None

    def _configurar_conexao(self):
        senhas_teste = [self.password] if self.password is not None else ["root", "", "1234", "123456", "admin"]

        for senha in senhas_teste:
            if self._testar_mysql(senha):
                self.password = senha
                self._garantir_banco_mysql()
                return

        self.modo = "sqlite"
        self._garantir_banco_sqlite()

    def _testar_mysql(self, senha):
        if pymysql is not None:
            try:
                conn = pymysql.connect(host=self.host, user=self.user, password=senha, charset="utf8mb4")
                conn.close()
                self.modo = "pymysql"
                return True
            except Exception:
                pass

        if mysql_connector is not None:
            try:
                conn = mysql_connector.connect(host=self.host, user=self.user, password=senha)
                conn.close()
                self.modo = "mysql_connector"
                return True
            except Exception:
                pass

        if self.mysql_bin:
            cmd = [self.mysql_bin, f"-h{self.host}", f"-u{self.user}"]
            if senha:
                cmd.append(f"-p{senha}")
            cmd.extend(["-e", "SELECT 1;"])
            res = subprocess.run(cmd, capture_output=True, text=True)
            if res.returncode == 0:
                self.modo = "mysql_cli"
                return True

        return False

    def _garantir_banco_mysql(self):
        ddl_statements = [
            f"CREATE DATABASE IF NOT EXISTS {self.database} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;",
            f"USE {self.database};",
            """CREATE TABLE IF NOT EXISTS Modalidades (
                id_modalidade INT AUTO_INCREMENT PRIMARY KEY,
                nome_modalidade VARCHAR(100) NOT NULL,
                preco_mensal DECIMAL(10, 2) NOT NULL,
                CONSTRAINT chk_preco_positivo CHECK (preco_mensal >= 0)
            ) ENGINE=InnoDB;""",
            """CREATE TABLE IF NOT EXISTS Alunos (
                id_aluno INT AUTO_INCREMENT PRIMARY KEY,
                nome_aluno VARCHAR(150) NOT NULL,
                cpf VARCHAR(11) NOT NULL UNIQUE,
                data_matricula DATE NOT NULL
            ) ENGINE=InnoDB;""",
            """CREATE TABLE IF NOT EXISTS Instrutores (
                id_instrutor INT AUTO_INCREMENT PRIMARY KEY,
                nome_instrutor VARCHAR(150) NOT NULL,
                cref VARCHAR(20) NOT NULL UNIQUE,
                id_modalidade INT NOT NULL,
                CONSTRAINT fk_instrutor_modalidade
                    FOREIGN KEY (id_modalidade) REFERENCES Modalidades(id_modalidade)
                    ON UPDATE CASCADE ON DELETE RESTRICT
            ) ENGINE=InnoDB;""",
            """CREATE TABLE IF NOT EXISTS ExamesMedicos (
                id_exame INT AUTO_INCREMENT PRIMARY KEY,
                data_avaliacao DATE NOT NULL,
                situacao ENUM('Apto', 'Inapto') NOT NULL,
                id_aluno INT NOT NULL UNIQUE,
                CONSTRAINT fk_exame_aluno
                    FOREIGN KEY (id_aluno) REFERENCES Alunos(id_aluno)
                    ON UPDATE CASCADE ON DELETE CASCADE
            ) ENGINE=InnoDB;""",
            """CREATE TABLE IF NOT EXISTS MatriculasModalidades (
                id_matricula_modalidade INT AUTO_INCREMENT PRIMARY KEY,
                data_adesao DATE NOT NULL,
                id_modalidade INT NOT NULL,
                id_aluno INT NOT NULL,
                CONSTRAINT fk_matricula_modalidade
                    FOREIGN KEY (id_modalidade) REFERENCES Modalidades(id_modalidade)
                    ON UPDATE CASCADE ON DELETE CASCADE,
                CONSTRAINT fk_matricula_aluno
                    FOREIGN KEY (id_aluno) REFERENCES Alunos(id_aluno)
                    ON UPDATE CASCADE ON DELETE CASCADE,
                CONSTRAINT uq_aluno_modalidade UNIQUE (id_aluno, id_modalidade)
            ) ENGINE=InnoDB;""",
        ]

        if self.modo == "pymysql":
            conn = pymysql.connect(host=self.host, user=self.user, password=self.password, charset="utf8mb4", autocommit=True)
            with conn.cursor() as cur:
                for stmt in ddl_statements:
                    cur.execute(stmt)
            conn.close()
        elif self.modo == "mysql_connector":
            conn = mysql_connector.connect(host=self.host, user=self.user, password=self.password, autocommit=True)
            cur = conn.cursor()
            for stmt in ddl_statements:
                cur.execute(stmt)
            cur.close()
            conn.close()
        elif self.modo == "mysql_cli":
            cmd = [self.mysql_bin, f"-h{self.host}", f"-u{self.user}"]
            if self.password:
                cmd.append(f"-p{self.password}")
            cmd.extend(["--default-character-set=utf8mb4", "-e", " ".join(ddl_statements)])
            subprocess.run(cmd, capture_output=True, text=True)

        qtd = self._executar_sql("SELECT COUNT(*) FROM Modalidades;", fetch=True)
        if qtd and int(qtd[0][0]) == 0:
            self._popular_dados_iniciais()

    def _garantir_banco_sqlite(self):
        with sqlite3.connect(self.sqlite_path) as conn:
            conn.execute("PRAGMA foreign_keys = ON;")
            conn.executescript("""
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
        qtd = self._executar_sql("SELECT COUNT(*) FROM Modalidades;", fetch=True)
        if qtd and int(qtd[0][0]) == 0:
            self._popular_dados_iniciais()

    def _popular_dados_iniciais(self):
        for nome, preco in [
            ("Musculação", 90.00), ("Crossfit", 150.00), ("Natação", 150.00),
            ("Pilates", 130.00), ("Boxe", 110.00),
        ]:
            self.salvar_modalidade(Modalidade(None, nome, preco))
        for nome, cpf, dt in [
            ("Helena Vieira", "99988877766", "2026-01-10"),
            ("Camila Ribeiro", "44433322211", "2026-02-15"),
            ("Jeremias Souza", "11122233344", "2026-03-30"),
            ("Lucas Silva", "55566677788", "2026-04-10"),
            ("Beatriz Lima", "22233344455", "2026-05-15"),
        ]:
            self.salvar_aluno(Aluno(None, nome, cpf, dt))
        for nome, cref, id_mod in [
            ("Professora Maria Clara Pastor", "CREF/SP 11111", 2),
            ("Professor Caio Polidoro", "CREF/SP 22222", 1),
            ("Professor Marcelo Costa", "CREF/SP 33333", 3),
            ("Professora Fernanda Souza", "CREF/SP 44444", 4),
            ("Professor Rodrigo Alves", "CREF/SP 55555", 5),
        ]:
            self.salvar_instrutor(Instrutor(None, nome, cref, id_mod))
        for dt, sit, id_al in [
            ("2026-01-09", "Apto", 1),
            ("2026-02-14", "Apto", 2),
            ("2026-04-14", "Inapto", 3),
            ("2026-04-09", "Apto", 4),
            ("2026-05-14", "Apto", 5),
        ]:
            self.salvar_exame(ExameMedico(None, dt, sit, id_al))
        for dt, id_mod, id_al in [
            ("2026-01-10", 1, 1),
            ("2026-01-20", 2, 1),
            ("2026-02-15", 2, 2),
            ("2026-05-15", 3, 3),
            ("2026-04-10", 1, 4),
            ("2026-04-12", 3, 4),
            ("2026-05-15", 4, 5),
        ]:
            self.salvar_matricula(MatriculaModalidade(None, dt, id_mod, id_al))

    def _executar_sql(self, sql, params=(), fetch=False):
        if self.modo == "pymysql":
            conn = pymysql.connect(
                host=self.host, user=self.user, password=self.password,
                database=self.database, charset="utf8mb4", autocommit=True
            )
            try:
                with conn.cursor() as cur:
                    cur.execute(sql, params)
                    if fetch:
                        return cur.fetchall()
                    conn.commit()
                    return cur.rowcount
            finally:
                conn.close()

        if self.modo == "mysql_connector":
            conn = mysql_connector.connect(
                host=self.host, user=self.user, password=self.password,
                database=self.database, autocommit=True
            )
            try:
                cur = conn.cursor()
                cur.execute(sql, params)
                if fetch:
                    rows = cur.fetchall()
                    cur.close()
                    return rows
                conn.commit()
                rc = cur.rowcount
                cur.close()
                return rc
            finally:
                conn.close()

        if self.modo == "mysql_cli":
            query_formatada = sql
            for p in params:
                if p is None:
                    val = "NULL"
                elif isinstance(p, (int, float)):
                    val = str(p)
                else:
                    escapado = str(p).replace("\\", "\\\\").replace("'", "\\'")
                    val = f"'{escapado}'"
                query_formatada = query_formatada.replace("%s", val, 1)

            if not fetch:
                query_formatada = query_formatada.rstrip(";") + "; SELECT ROW_COUNT();"

            cmd = [self.mysql_bin, f"-h{self.host}", f"-u{self.user}"]
            if self.password:
                cmd.append(f"-p{self.password}")
            cmd.extend([
                "--default-character-set=utf8mb4", "--batch", "--raw",
                "--skip-column-names", "-D", self.database, "-e", query_formatada
            ])
            res = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")
            if res.returncode != 0:
                erro = "\n".join(l for l in res.stderr.splitlines() if "Using a password on the command line" not in l)
                raise RuntimeError(erro.strip() or "Erro ao executar SQL no MySQL.")
            linhas = [l.split("\t") for l in res.stdout.splitlines() if l.strip()]
            if fetch:
                return linhas
            return int(linhas[-1][0]) if linhas else 0

        sql_sqlite = sql.replace("%s", "?")
        with sqlite3.connect(self.sqlite_path) as conn:
            conn.execute("PRAGMA foreign_keys = ON;")
            cur = conn.cursor()
            cur.execute(sql_sqlite, params)
            if fetch:
                return cur.fetchall()
            conn.commit()
            return cur.rowcount

    def salvar_modalidade(self, modalidade: Modalidade):
        self._executar_sql(
            "INSERT INTO Modalidades (nome_modalidade, preco_mensal) VALUES (%s, %s);",
            (modalidade.nome, modalidade.precoMensal),
        )

    def atualizar_modalidade(self, modalidade: Modalidade):
        return self._executar_sql(
            "UPDATE Modalidades SET nome_modalidade = %s, preco_mensal = %s WHERE id_modalidade = %s;",
            (modalidade.nome, modalidade.precoMensal, modalidade.idModalidade),
        ) > 0

    def listar_modalidades(self):
        rows = self._executar_sql(
            "SELECT id_modalidade, nome_modalidade, preco_mensal FROM Modalidades ORDER BY id_modalidade;",
            fetch=True,
        )
        return [Modalidade(r[0], r[1], r[2]) for r in rows]

    def excluir_modalidade(self, id_modalidade: int):
        return self._executar_sql(
            "DELETE FROM Modalidades WHERE id_modalidade = %s;",
            (id_modalidade,),
        ) > 0

    def salvar_instrutor(self, instrutor: Instrutor):
        self._executar_sql(
            "INSERT INTO Instrutores (nome_instrutor, cref, id_modalidade) VALUES (%s, %s, %s);",
            (instrutor.nome, instrutor.cref, instrutor.idModalidade),
        )

    def atualizar_instrutor(self, instrutor: Instrutor):
        return self._executar_sql(
            "UPDATE Instrutores SET nome_instrutor = %s, cref = %s, id_modalidade = %s WHERE id_instrutor = %s;",
            (instrutor.nome, instrutor.cref, instrutor.idModalidade, instrutor.idInstrutor),
        ) > 0

    def listar_instrutores(self):
        rows = self._executar_sql(
            "SELECT id_instrutor, nome_instrutor, cref, id_modalidade FROM Instrutores ORDER BY id_instrutor;",
            fetch=True,
        )
        return [Instrutor(r[0], r[1], r[2], r[3]) for r in rows]

    def excluir_instrutor(self, id_instrutor: int):
        return self._executar_sql(
            "DELETE FROM Instrutores WHERE id_instrutor = %s;",
            (id_instrutor,),
        ) > 0

    def salvar_aluno(self, aluno: Aluno):
        self._executar_sql(
            "INSERT INTO Alunos (nome_aluno, cpf, data_matricula) VALUES (%s, %s, %s);",
            (aluno.nome, aluno.cpf, aluno.dataMatricula),
        )

    def atualizar_aluno(self, aluno: Aluno):
        return self._executar_sql(
            "UPDATE Alunos SET nome_aluno = %s, cpf = %s, data_matricula = %s WHERE id_aluno = %s;",
            (aluno.nome, aluno.cpf, aluno.dataMatricula, aluno.idAluno),
        ) > 0

    def listar_alunos(self):
        rows = self._executar_sql(
            "SELECT id_aluno, nome_aluno, cpf, data_matricula FROM Alunos ORDER BY id_aluno;",
            fetch=True,
        )
        return [Aluno(r[0], r[1], r[2], r[3]) for r in rows]

    def excluir_aluno(self, id_aluno: int):
        return self._executar_sql(
            "DELETE FROM Alunos WHERE id_aluno = %s;",
            (id_aluno,),
        ) > 0

    def salvar_matricula(self, matricula: MatriculaModalidade):
        self._executar_sql(
            "INSERT INTO MatriculasModalidades (data_adesao, id_modalidade, id_aluno) VALUES (%s, %s, %s);",
            (matricula.dataAdesao, matricula.idModalidade, matricula.idAluno),
        )

    def atualizar_matricula(self, matricula: MatriculaModalidade):
        return self._executar_sql(
            "UPDATE MatriculasModalidades SET data_adesao = %s, id_modalidade = %s, id_aluno = %s WHERE id_matricula_modalidade = %s;",
            (matricula.dataAdesao, matricula.idModalidade, matricula.idAluno, matricula.idMatriculaModalidade),
        ) > 0

    def listar_matriculas(self):
        rows = self._executar_sql(
            "SELECT id_matricula_modalidade, data_adesao, id_modalidade, id_aluno FROM MatriculasModalidades ORDER BY id_matricula_modalidade;",
            fetch=True,
        )
        return [MatriculaModalidade(r[0], r[1], r[2], r[3]) for r in rows]

    def excluir_matricula(self, id_matricula: int):
        return self._executar_sql(
            "DELETE FROM MatriculasModalidades WHERE id_matricula_modalidade = %s;",
            (id_matricula,),
        ) > 0

    def salvar_exame(self, exame: ExameMedico):
        self._executar_sql(
            "INSERT INTO ExamesMedicos (data_avaliacao, situacao, id_aluno) VALUES (%s, %s, %s);",
            (exame.dataAvaliacao, exame.situacao, exame.idAluno),
        )

    def atualizar_exame(self, id_exame, data_avaliacao, situacao, id_aluno):
        exame = ExameMedico(id_exame, data_avaliacao, situacao, id_aluno)
        return self._executar_sql(
            "UPDATE ExamesMedicos SET data_avaliacao = %s, situacao = %s, id_aluno = %s WHERE id_exame = %s;",
            (exame.dataAvaliacao, exame.situacao, exame.idAluno, exame.idExame),
        ) > 0

    def listar_exames(self):
        rows = self._executar_sql(
            "SELECT id_exame, data_avaliacao, situacao, id_aluno FROM ExamesMedicos ORDER BY id_exame;",
            fetch=True,
        )
        return [ExameMedico(r[0], r[1], r[2], r[3]) for r in rows]

    def excluir_exame(self, id_exame: int):
        return self._executar_sql(
            "DELETE FROM ExamesMedicos WHERE id_exame = %s;",
            (id_exame,),
        ) > 0

    # ------------------------------------------------------------------
    # SELEÇÕES COMPLEXAS (junção de tabelas + filtros de condição)
    # Retornam listas de dicionários, pois cruzam várias entidades.
    # ------------------------------------------------------------------
    def _group_concat(self, coluna):
        # MySQL usa SEPARATOR; o SQLite usa o segundo argumento
        if self.modo == "sqlite":
            return f"GROUP_CONCAT({coluna}, ', ')"
        return f"GROUP_CONCAT({coluna} SEPARATOR ', ')"

    def consulta_alunos_aptos(self, preco_minimo=90.00):
        """Consulta 1: junção de 5 tabelas, filtrando exame Apto e mensalidade mínima."""
        rows = self._executar_sql(
            """SELECT a.nome_aluno, a.cpf, m.nome_modalidade, m.preco_mensal,
                      i.nome_instrutor, i.cref, em.situacao, mm.data_adesao
               FROM Alunos a
               INNER JOIN MatriculasModalidades mm ON a.id_aluno = mm.id_aluno
               INNER JOIN Modalidades m ON mm.id_modalidade = m.id_modalidade
               INNER JOIN Instrutores i ON m.id_modalidade = i.id_modalidade
               INNER JOIN ExamesMedicos em ON a.id_aluno = em.id_aluno
               WHERE em.situacao = 'Apto'
                 AND m.preco_mensal >= %s
               ORDER BY a.nome_aluno ASC, m.nome_modalidade ASC;""",
            (preco_minimo,), fetch=True,
        )
        return [
            {"aluno": r[0], "cpf": r[1], "modalidade": r[2], "mensalidade": float(r[3]),
             "instrutor": r[4], "cref": r[5], "situacao": r[6], "data_adesao": str(r[7])}
            for r in rows
        ]

    def consulta_alunos_inaptos(self):
        """Consulta 2: alunos matriculados com exame Inapto (junção de 5 tabelas)."""
        rows = self._executar_sql(
            """SELECT a.id_aluno, a.nome_aluno, em.situacao, em.data_avaliacao,
                      m.nome_modalidade, i.nome_instrutor
               FROM Alunos a
               INNER JOIN ExamesMedicos em ON a.id_aluno = em.id_aluno
               INNER JOIN MatriculasModalidades mm ON a.id_aluno = mm.id_aluno
               INNER JOIN Modalidades m ON mm.id_modalidade = m.id_modalidade
               INNER JOIN Instrutores i ON m.id_modalidade = i.id_modalidade
               WHERE em.situacao = 'Inapto'
               ORDER BY a.nome_aluno ASC;""",
            fetch=True,
        )
        return [
            {"id_aluno": int(r[0]), "aluno": r[1], "situacao": r[2], "data_avaliacao": str(r[3]),
             "modalidade": r[4], "instrutor": r[5]}
            for r in rows
        ]

    def consulta_receita_por_modalidade(self):
        """Consulta 3: LEFT JOIN + GROUP BY + COUNT/SUM + HAVING (só modalidades com aluno)."""
        rows = self._executar_sql(
            """SELECT m.id_modalidade, m.nome_modalidade, i.nome_instrutor, m.preco_mensal,
                      COUNT(mm.id_aluno) AS total_alunos,
                      SUM(m.preco_mensal) AS receita_mensal
               FROM Modalidades m
               LEFT JOIN Instrutores i ON m.id_modalidade = i.id_modalidade
               LEFT JOIN MatriculasModalidades mm ON m.id_modalidade = mm.id_modalidade
               GROUP BY m.id_modalidade, m.nome_modalidade, i.nome_instrutor, m.preco_mensal
               HAVING COUNT(mm.id_aluno) > 0
               ORDER BY SUM(m.preco_mensal) DESC, m.nome_modalidade ASC;""",
            fetch=True,
        )
        return [
            {"id_modalidade": int(r[0]), "modalidade": r[1], "instrutor": r[2] or "-",
             "preco_mensal": float(r[3]), "total_alunos": int(r[4]), "receita_mensal": float(r[5])}
            for r in rows
        ]

    def consulta_alunos_multimodalidade(self):
        """Consulta 4: alunos em mais de uma modalidade (GROUP BY + HAVING > 1)."""
        rows = self._executar_sql(
            f"""SELECT a.id_aluno, a.nome_aluno,
                       COUNT(mm.id_modalidade) AS qtd_modalidades,
                       {self._group_concat("m.nome_modalidade")} AS modalidades,
                       SUM(m.preco_mensal) AS mensalidade_total
                FROM Alunos a
                INNER JOIN MatriculasModalidades mm ON a.id_aluno = mm.id_aluno
                INNER JOIN Modalidades m ON mm.id_modalidade = m.id_modalidade
                GROUP BY a.id_aluno, a.nome_aluno
                HAVING COUNT(mm.id_modalidade) > 1
                ORDER BY SUM(m.preco_mensal) DESC, a.nome_aluno ASC;""",
            fetch=True,
        )
        return [
            {"id_aluno": int(r[0]), "aluno": r[1], "qtd_modalidades": int(r[2]),
             "modalidades": r[3], "mensalidade_total": float(r[4])}
            for r in rows
        ]


class Controlador:
    def __init__(self):
        self.adaptador = AdaptadorMapaObjetoRelacional()

    def cadastrar_modalidade(self, nome, preco_mensal):
        modalidade = Modalidade(None, nome, preco_mensal)
        self.adaptador.salvar_modalidade(modalidade)

    def editar_modalidade(self, id_modalidade, nome, preco_mensal):
        modalidade = Modalidade(id_modalidade, nome, preco_mensal)
        return self.adaptador.atualizar_modalidade(modalidade)

    def obter_modalidades(self):
        return self.adaptador.listar_modalidades()

    def remover_modalidade(self, id_modalidade):
        return self.adaptador.excluir_modalidade(id_modalidade)

    def cadastrar_instrutor(self, nome, cref, id_modalidade):
        instrutor = Instrutor(None, nome, cref, id_modalidade)
        self.adaptador.salvar_instrutor(instrutor)

    def editar_instrutor(self, id_instrutor, nome, cref, id_modalidade):
        instrutor = Instrutor(id_instrutor, nome, cref, id_modalidade)
        return self.adaptador.atualizar_instrutor(instrutor)

    def obter_instrutores(self):
        return self.adaptador.listar_instrutores()

    def remover_instrutor(self, id_instrutor):
        return self.adaptador.excluir_instrutor(id_instrutor)

    def cadastrar_aluno(self, nome, cpf, data_matricula):
        aluno = Aluno(None, nome, cpf, data_matricula)
        self.adaptador.salvar_aluno(aluno)

    def editar_aluno(self, id_aluno, nome, cpf, data_matricula):
        aluno = Aluno(id_aluno, nome, cpf, data_matricula)
        return self.adaptador.atualizar_aluno(aluno)

    def obter_alunos(self):
        return self.adaptador.listar_alunos()

    def remover_aluno(self, id_aluno):
        return self.adaptador.excluir_aluno(id_aluno)

    def cadastrar_matricula(self, data_adesao, id_modalidade, id_aluno):
        matricula = MatriculaModalidade(None, data_adesao, id_modalidade, id_aluno)
        self.adaptador.salvar_matricula(matricula)

    def editar_matricula(self, id_matricula, data_adesao, id_modalidade, id_aluno):
        matricula = MatriculaModalidade(id_matricula, data_adesao, id_modalidade, id_aluno)
        return self.adaptador.atualizar_matricula(matricula)

    def obter_matriculas(self):
        return self.adaptador.listar_matriculas()

    def remover_matricula(self, id_matricula):
        return self.adaptador.excluir_matricula(id_matricula)

    def cadastrar_exame(self, data_avaliacao, situacao, id_aluno):
        exame = ExameMedico(None, data_avaliacao, situacao, id_aluno)
        self.adaptador.salvar_exame(exame)

    def editar_exame(self, id_exame, data_avaliacao, situacao, id_aluno):
        return self.adaptador.atualizar_exame(id_exame, data_avaliacao, situacao, id_aluno)

    def obter_exames(self):
        return self.adaptador.listar_exames()

    def remover_exame(self, id_exame):
        return self.adaptador.excluir_exame(id_exame)

    def relatorio_alunos_aptos(self, preco_minimo=90.00):
        return self.adaptador.consulta_alunos_aptos(preco_minimo)

    def relatorio_alunos_inaptos(self):
        return self.adaptador.consulta_alunos_inaptos()

    def relatorio_receita_por_modalidade(self):
        return self.adaptador.consulta_receita_por_modalidade()

    def relatorio_alunos_multimodalidade(self):
        return self.adaptador.consulta_alunos_multimodalidade()


class InteracaoUsuario:
    def __init__(self):
        self.controlador = Controlador()

    def menu_principal(self):
        while True:
            print()
            opcao = questionary.select(
                "SISTEMA DE ACADEMIA / CENTRO ESPORTIVO - Escolha uma opção:",
                choices=[
                    Choice("1 - Modalidades", value="1"),
                    Choice("2 - Instrutores (1:N)", value="2"),
                    Choice("3 - Alunos", value="3"),
                    Choice("4 - Matrículas em Modalidades (N:N)", value="4"),
                    Choice("5 - Exames Médicos (1:1)", value="5"),
                    Choice("6 - Consultas (seleções complexas)", value="6"),
                    Choice("0 - Sair", value="0"),
                ],
                qmark="",
            ).ask()

            if opcao == "1":
                self.menu_modalidades()
            elif opcao == "2":
                self.menu_instrutores()
            elif opcao == "3":
                self.menu_alunos()
            elif opcao == "4":
                self.menu_matriculas()
            elif opcao == "5":
                self.menu_exames()
            elif opcao == "6":
                self.menu_consultas()
            elif opcao == "0" or opcao is None:
                print("Encerrando o sistema...")
                break

    def _escolher_modalidade(self, mensagem="Selecione a modalidade:"):
        modalidades = self.controlador.obter_modalidades()
        if not modalidades:
            print("Nenhuma modalidade cadastrada.")
            return None
        opcoes = [
            Choice(f"ID {m.idModalidade} - {m.nome} (R$ {m.precoMensal:.2f})", value=m)
            for m in modalidades
        ]
        opcoes.append(Choice("Cancelar / Voltar", value=False))
        return questionary.select(mensagem, choices=opcoes, qmark="").ask()

    def _escolher_aluno(self, mensagem="Selecione o aluno:"):
        alunos = self.controlador.obter_alunos()
        if not alunos:
            print("Nenhum aluno cadastrado.")
            return None
        opcoes = [
            Choice(f"ID {a.idAluno} - {a.nome} (CPF: {a.cpf})", value=a)
            for a in alunos
        ]
        opcoes.append(Choice("Cancelar / Voltar", value=False))
        return questionary.select(mensagem, choices=opcoes, qmark="").ask()

    def menu_modalidades(self):
        op = questionary.select(
            "MODALIDADES - O que deseja fazer?",
            choices=[
                Choice("Listar Modalidades", value="1"),
                Choice("Cadastrar Modalidade", value="2"),
                Choice("Atualizar Modalidade", value="3"),
                Choice("Excluir Modalidade", value="4"),
                Choice("Voltar", value="0"),
            ],
            qmark="",
        ).ask()

        if op == "1":
            print("\n--- LISTA DE MODALIDADES ---")
            for m in self.controlador.obter_modalidades():
                print(f"ID: {m.idModalidade} | Nome: {m.nome} | Preço Mensal: R$ {m.precoMensal:.2f}")
        elif op == "2":
            try:
                nome = questionary.text("Nome da modalidade:", qmark="").ask()
                preco_str = questionary.text("Preço mensal (R$):", qmark="").ask()
                if nome and preco_str:
                    preco = float(preco_str.replace(",", "."))
                    self.controlador.cadastrar_modalidade(nome.strip(), preco)
                    print("Modalidade salva no banco com sucesso!")
            except Exception as e:
                print(f"Erro ao cadastrar modalidade: {e}")
        elif op == "3":
            try:
                mod = self._escolher_modalidade("Selecione a modalidade para atualizar:")
                if mod:
                    nome = questionary.text("Novo nome da modalidade:", default=mod.nome, qmark="").ask()
                    preco_str = questionary.text("Novo preço mensal:", default=f"{mod.precoMensal:.2f}", qmark="").ask()
                    if nome and preco_str:
                        preco = float(preco_str.replace(",", "."))
                        self.controlador.editar_modalidade(mod.idModalidade, nome.strip(), preco)
                        print("Modalidade atualizada com sucesso!")
            except Exception as e:
                print(f"Erro ao atualizar modalidade: {e}")
        elif op == "4":
            try:
                mod = self._escolher_modalidade("Selecione a modalidade para excluir:")
                if mod:
                    if self.controlador.remover_modalidade(mod.idModalidade):
                        print("Modalidade excluída com sucesso!")
            except Exception as e:
                print(f"Erro ao excluir (verifique se há instrutor vinculado - 1:N): {e}")

    def menu_instrutores(self):
        op = questionary.select(
            "INSTRUTORES (1:N com Modalidade) - O que deseja fazer?",
            choices=[
                Choice("Listar Instrutores", value="1"),
                Choice("Cadastrar Instrutor", value="2"),
                Choice("Atualizar Instrutor", value="3"),
                Choice("Excluir Instrutor", value="4"),
                Choice("Voltar", value="0"),
            ],
            qmark="",
        ).ask()

        if op == "1":
            print("\n--- LISTA DE INSTRUTORES ---")
            for i in self.controlador.obter_instrutores():
                print(f"ID: {i.idInstrutor} | Nome: {i.nome} | CREF: {i.cref} | ID Modalidade: {i.idModalidade}")
        elif op == "2":
            try:
                nome = questionary.text("Nome do instrutor:", qmark="").ask()
                cref = questionary.text("CREF:", qmark="").ask()
                mod = self._escolher_modalidade("Selecione a modalidade que o instrutor leciona:")
                if nome and cref and mod:
                    self.controlador.cadastrar_instrutor(nome.strip(), cref.strip(), mod.idModalidade)
                    print("Instrutor salvo no banco com sucesso!")
            except Exception as e:
                print(f"Erro ao cadastrar instrutor: {e}")
        elif op == "3":
            try:
                instrutores = self.controlador.obter_instrutores()
                if not instrutores:
                    print("Nenhum instrutor cadastrado.")
                    return
                opcoes = [
                    Choice(f"ID {i.idInstrutor} - {i.nome} ({i.cref}) | Mod ID: {i.idModalidade}", value=i)
                    for i in instrutores
                ]
                opcoes.append(Choice("Cancelar / Voltar", value=False))
                inst = questionary.select("Selecione o instrutor para atualizar:", choices=opcoes, qmark="").ask()
                if inst:
                    nome = questionary.text("Novo nome do instrutor:", default=inst.nome, qmark="").ask()
                    cref = questionary.text("Novo CREF:", default=inst.cref, qmark="").ask()
                    mod = self._escolher_modalidade("Selecione a nova modalidade:")
                    if nome and cref and mod:
                        self.controlador.editar_instrutor(inst.idInstrutor, nome.strip(), cref.strip(), mod.idModalidade)
                        print("Instrutor atualizado com sucesso!")
            except Exception as e:
                print(f"Erro ao atualizar instrutor: {e}")
        elif op == "4":
            try:
                instrutores = self.controlador.obter_instrutores()
                if not instrutores:
                    print("Nenhum instrutor cadastrado.")
                    return
                opcoes = [
                    Choice(f"ID {i.idInstrutor} - {i.nome} ({i.cref})", value=i)
                    for i in instrutores
                ]
                opcoes.append(Choice("Cancelar / Voltar", value=False))
                inst = questionary.select("Selecione o instrutor para excluir:", choices=opcoes, qmark="").ask()
                if inst:
                    if self.controlador.remover_instrutor(inst.idInstrutor):
                        print("Instrutor excluído com sucesso!")
            except Exception as e:
                print(f"Erro: {e}")

    def menu_alunos(self):
        op = questionary.select(
            "ALUNOS - O que deseja fazer?",
            choices=[
                Choice("Listar Alunos", value="1"),
                Choice("Cadastrar Aluno", value="2"),
                Choice("Atualizar Aluno", value="3"),
                Choice("Excluir Aluno", value="4"),
                Choice("Voltar", value="0"),
            ],
            qmark="",
        ).ask()

        if op == "1":
            print("\n--- LISTA DE ALUNOS ---")
            for a in self.controlador.obter_alunos():
                print(f"ID: {a.idAluno} | Nome: {a.nome} | CPF: {a.cpf} | Data Matrícula: {a.dataMatricula}")
        elif op == "2":
            try:
                nome = questionary.text("Nome do aluno:", qmark="").ask()
                cpf = questionary.text("CPF (11 dígitos):", qmark="").ask()
                data_mat = questionary.text("Data de matrícula (AAAA-MM-DD):", qmark="").ask()
                if nome and cpf and data_mat:
                    self.controlador.cadastrar_aluno(nome.strip(), cpf.strip(), data_mat.strip())
                    print("Aluno salvo no banco com sucesso!")
            except Exception as e:
                print(f"Erro ao cadastrar aluno: {e}")
        elif op == "3":
            try:
                aluno = self._escolher_aluno("Selecione o aluno para atualizar:")
                if aluno:
                    nome = questionary.text("Novo nome do aluno:", default=aluno.nome, qmark="").ask()
                    cpf = questionary.text("Novo CPF (11 dígitos):", default=aluno.cpf, qmark="").ask()
                    data_mat = questionary.text("Nova data de matrícula (AAAA-MM-DD):", default=aluno.dataMatricula, qmark="").ask()
                    if nome and cpf and data_mat:
                        self.controlador.editar_aluno(aluno.idAluno, nome.strip(), cpf.strip(), data_mat.strip())
                        print("Aluno atualizado com sucesso!")
            except Exception as e:
                print(f"Erro ao atualizar aluno: {e}")
        elif op == "4":
            try:
                aluno = self._escolher_aluno("Selecione o aluno para excluir:")
                if aluno:
                    if self.controlador.remover_aluno(aluno.idAluno):
                        print("Aluno excluído com sucesso (matrículas e exame removidos em cascata).")
            except Exception as e:
                print(f"Erro: {e}")

    def menu_matriculas(self):
        op = questionary.select(
            "MATRÍCULAS EM MODALIDADES (N:N) - O que deseja fazer?",
            choices=[
                Choice("Listar Matrículas", value="1"),
                Choice("Realizar Matrícula", value="2"),
                Choice("Atualizar Matrícula", value="3"),
                Choice("Cancelar Matrícula", value="4"),
                Choice("Voltar", value="0"),
            ],
            qmark="",
        ).ask()

        if op == "1":
            print("\n--- LISTA DE MATRÍCULAS ---")
            for mm in self.controlador.obter_matriculas():
                print(
                    f"ID: {mm.idMatriculaModalidade} | Data Adesão: {mm.dataAdesao} "
                    f"| ID Modalidade: {mm.idModalidade} | ID Aluno: {mm.idAluno}"
                )
        elif op == "2":
            try:
                aluno = self._escolher_aluno("Selecione o aluno para matricular:")
                if not aluno:
                    return
                mod = self._escolher_modalidade("Selecione a modalidade:")
                if not mod:
                    return
                data_adesao = questionary.text("Data de adesão (AAAA-MM-DD):", qmark="").ask()
                if data_adesao:
                    self.controlador.cadastrar_matricula(data_adesao.strip(), mod.idModalidade, aluno.idAluno)
                    print("Matrícula salva no banco com sucesso!")
            except Exception as e:
                print(f"Erro ao realizar matrícula: {e}")
        elif op == "3":
            try:
                matriculas = self.controlador.obter_matriculas()
                if not matriculas:
                    print("Nenhuma matrícula cadastrada.")
                    return
                opcoes = [
                    Choice(
                        f"ID {mm.idMatriculaModalidade} | Aluno ID: {mm.idAluno} | Mod ID: {mm.idModalidade} | Adesão: {mm.dataAdesao}",
                        value=mm,
                    )
                    for mm in matriculas
                ]
                opcoes.append(Choice("Cancelar / Voltar", value=False))
                mat = questionary.select("Selecione a matrícula para atualizar:", choices=opcoes, qmark="").ask()
                if mat:
                    aluno = self._escolher_aluno("Selecione o novo aluno:")
                    mod = self._escolher_modalidade("Selecione a nova modalidade:")
                    data_adesao = questionary.text("Nova data de adesão (AAAA-MM-DD):", default=mat.dataAdesao, qmark="").ask()
                    if aluno and mod and data_adesao:
                        self.controlador.editar_matricula(
                            mat.idMatriculaModalidade, data_adesao.strip(), mod.idModalidade, aluno.idAluno
                        )
                        print("Matrícula atualizada com sucesso!")
            except Exception as e:
                print(f"Erro ao atualizar matrícula: {e}")
        elif op == "4":
            try:
                matriculas = self.controlador.obter_matriculas()
                if not matriculas:
                    print("Nenhuma matrícula cadastrada.")
                    return
                opcoes = [
                    Choice(
                        f"ID {mm.idMatriculaModalidade} | Aluno ID: {mm.idAluno} | Mod ID: {mm.idModalidade} | Adesão: {mm.dataAdesao}",
                        value=mm,
                    )
                    for mm in matriculas
                ]
                opcoes.append(Choice("Cancelar / Voltar", value=False))
                mat = questionary.select("Selecione a matrícula para cancelar:", choices=opcoes, qmark="").ask()
                if mat:
                    if self.controlador.remover_matricula(mat.idMatriculaModalidade):
                        print("Matrícula cancelada com sucesso!")
            except Exception as e:
                print(f"Erro: {e}")

    def menu_exames(self):
        op = questionary.select(
            "EXAMES MÉDICOS (1:1 com Aluno) - O que deseja fazer?",
            choices=[
                Choice("Listar Exames Médicos", value="1"),
                Choice("Cadastrar Exame Médico", value="2"),
                Choice("Atualizar Exame Médico", value="3"),
                Choice("Excluir Exame Médico", value="4"),
                Choice("Voltar", value="0"),
            ],
            qmark="",
        ).ask()

        if op == "1":
            print("\n--- LISTA DE EXAMES MÉDICOS ---")
            for ex in self.controlador.obter_exames():
                print(
                    f"ID: {ex.idExame} | Data Avaliação: {ex.dataAvaliacao} "
                    f"| Situação: {ex.situacao} | ID Aluno: {ex.idAluno}"
                )
        elif op == "2":
            try:
                aluno = self._escolher_aluno("Selecione o aluno para o exame médico:")
                if not aluno:
                    return
                data_aval = questionary.text("Data da avaliação (AAAA-MM-DD):", qmark="").ask()
                situacao = questionary.select(
                    "Situação médica:",
                    choices=["Apto", "Inapto"],
                    qmark="",
                ).ask()
                if data_aval and situacao:
                    self.controlador.cadastrar_exame(data_aval.strip(), situacao, aluno.idAluno)
                    print("Exame médico salvo no banco com sucesso!")
            except Exception as e:
                print(f"Erro ao cadastrar exame médico: {e}")
        elif op == "3":
            try:
                exames = self.controlador.obter_exames()
                if not exames:
                    print("Nenhum exame cadastrado.")
                    return
                opcoes = [
                    Choice(
                        f"ID {ex.idExame} | Aluno ID: {ex.idAluno} | Situação: {ex.situacao} | Data: {ex.dataAvaliacao}",
                        value=ex,
                    )
                    for ex in exames
                ]
                opcoes.append(Choice("Cancelar / Voltar", value=False))
                ex = questionary.select("Selecione o exame médico para atualizar:", choices=opcoes, qmark="").ask()
                if ex:
                    data_aval = questionary.text("Nova data da avaliação (AAAA-MM-DD):", default=ex.dataAvaliacao, qmark="").ask()
                    situacao = questionary.select(
                        "Nova situação médica:",
                        choices=["Apto", "Inapto"],
                        default=ex.situacao,
                        qmark="",
                    ).ask()
                    if data_aval and situacao:
                        self.controlador.editar_exame(ex.idExame, data_aval.strip(), situacao, ex.idAluno)
                        print("Exame médico atualizado com sucesso!")
            except Exception as e:
                print(f"Erro ao atualizar exame médico: {e}")
        elif op == "4":
            try:
                exames = self.controlador.obter_exames()
                if not exames:
                    print("Nenhum exame cadastrado.")
                    return
                opcoes = [
                    Choice(
                        f"ID {ex.idExame} | Aluno ID: {ex.idAluno} | Situação: {ex.situacao} | Data: {ex.dataAvaliacao}",
                        value=ex,
                    )
                    for ex in exames
                ]
                opcoes.append(Choice("Cancelar / Voltar", value=False))
                ex = questionary.select("Selecione o exame médico para excluir:", choices=opcoes, qmark="").ask()
                if ex:
                    if self.controlador.remover_exame(ex.idExame):
                        print("Exame médico excluído com sucesso!")
            except Exception as e:
                print(f"Erro: {e}")

    @staticmethod
    def _data_br(data):
        # "2026-01-10" -> "10/01/2026"
        partes = str(data)[:10].split("-")
        return "/".join(reversed(partes)) if len(partes) == 3 else str(data)

    def menu_consultas(self):
        op = questionary.select(
            "CONSULTAS (SELEÇÕES COMPLEXAS) - Escolha uma consulta:",
            choices=[
                Choice("1 - Ficha de alunos aptos (junção de 5 tabelas)", value="1"),
                Choice("2 - Auditoria médica: alunos inaptos matriculados", value="2"),
                Choice("3 - Receita e quantidade de alunos por modalidade", value="3"),
                Choice("4 - Alunos em mais de uma modalidade", value="4"),
                Choice("Voltar", value="0"),
            ],
            qmark="",
        ).ask()

        try:
            if op == "1":
                preco_str = questionary.text("Mensalidade mínima (R$):", default="90.00", qmark="").ask()
                if preco_str is None:
                    return
                preco = float(preco_str.replace(",", ".") or 0)
                linhas = self.controlador.relatorio_alunos_aptos(preco)
                print(f"\n--- ALUNOS APTOS COM MENSALIDADE A PARTIR DE R$ {preco:.2f} ---")
                for l in linhas:
                    print(
                        f"Aluno: {l['aluno']} | CPF: {l['cpf']} | Modalidade: {l['modalidade']} "
                        f"| Mensalidade: R$ {l['mensalidade']:.2f} | Instrutor: {l['instrutor']} ({l['cref']}) "
                        f"| Exame: {l['situacao']} | Adesão: {self._data_br(l['data_adesao'])}"
                    )
            elif op == "2":
                linhas = self.controlador.relatorio_alunos_inaptos()
                print("\n--- AUDITORIA MÉDICA: ALUNOS INAPTOS MATRICULADOS ---")
                for l in linhas:
                    print(
                        f"ID: {l['id_aluno']} | Aluno: {l['aluno']} | Exame: {l['situacao']} "
                        f"| Avaliação: {self._data_br(l['data_avaliacao'])} | Modalidade: {l['modalidade']} "
                        f"| Instrutor a avisar: {l['instrutor']}"
                    )
            elif op == "3":
                linhas = self.controlador.relatorio_receita_por_modalidade()
                print("\n--- RECEITA MENSAL E ALUNOS POR MODALIDADE ---")
                for l in linhas:
                    print(
                        f"Modalidade: {l['modalidade']} | Instrutor: {l['instrutor']} "
                        f"| Valor: R$ {l['preco_mensal']:.2f} | Alunos: {l['total_alunos']} "
                        f"| Receita mensal: R$ {l['receita_mensal']:.2f}"
                    )
            elif op == "4":
                linhas = self.controlador.relatorio_alunos_multimodalidade()
                print("\n--- ALUNOS EM MAIS DE UMA MODALIDADE ---")
                for l in linhas:
                    print(
                        f"ID: {l['id_aluno']} | Aluno: {l['aluno']} | Qtd. modalidades: {l['qtd_modalidades']} "
                        f"| Modalidades: {l['modalidades']} | Mensalidade total: R$ {l['mensalidade_total']:.2f}"
                    )
            else:
                return
            if not linhas:
                print("Nenhum registro encontrado.")
        except Exception as e:
            print(f"Erro ao executar consulta: {e}")


if __name__ == "__main__":
    ui = InteracaoUsuario()
    ui.menu_principal()
