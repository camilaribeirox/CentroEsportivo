# Sistema de Centro Esportivo

**Instituição:** IFSP – Câmpus Jacareí  
**Curso:** Tecnologia em Análise e Desenvolvimento de Sistemas (ADS)  
**Disciplina:** Banco de Dados 2 (2026)  
**Docente:** Prof. Raul E. S. Castanhari  
**Integrantes:** Camila R. Ribeiro, Helena Vieira e Maria Clara Pastor  

---

## Sobre o Projeto

Implementação de um **Sistema de Centro Esportivo** com modelagem conceitual (DER), modelo lógico relacional, script completo em **MySQL 8** e uma aplicação interativa no terminal em **Python**, estruturada em camadas com Mapeamento Objeto-Relacional (`AdaptadorMapaObjetoRelacional`).

### Entidades e Relacionamentos
- **`Modalidades`**: esportes oferecidos e preço mensal (`CHECK (preco_mensal >= 0)`).
- **`Instrutores`** (`1:N` com `Modalidades`): cada instrutor leciona uma modalidade e tem CREF único (`ON DELETE RESTRICT`).
- **`Alunos`**: cadastro de alunos com CPF único e data de matrícula.
- **`MatriculasModalidades`** (`N:N` entre `Alunos` e `Modalidades`): guarda a data de adesão (`data_adesao`) e impede matrícula duplicada do mesmo aluno na mesma modalidade (`UNIQUE (id_aluno, id_modalidade)` e `ON DELETE CASCADE`).
- **`ExamesMedicos`** (`1:1` com `Alunos`): um exame médico por aluno, `Apto` ou `Inapto` (`UNIQUE (id_aluno)` e `ON DELETE CASCADE`).

---

## 📂 Estrutura do Repositório

```
├── README.md
├── Relatório - Sistema Centro Esportivo.pdf   → relatório técnico
├── Slides Apresentação.pdf                     → slides da apresentação
├── diagramas/                                  → DER, modelo relacional e diagramas de classes
└── Sistema Centro Esportivo/
    ├── app.py                                  → aplicação em Python
    ├── centro_esportivo.sql                    → script completo em MySQL 8
    └── requirements.txt                        → dependências (questionary e pymysql)
```

---

## Diagramas

- [Diagrama Entidade-Relacionamento (DER)](diagramas/der.png)
- [Modelo Lógico Relacional](diagramas/modelo_relacional.png)
- [Diagrama de Classes de Domínio](diagramas/diagrama_classes_dominio.png)
- [Arquitetura de Persistência (ORM)](diagramas/diagrama_classes_arquitetura.png)

---

## Arquitetura da Aplicação (`app.py`)

A aplicação segue a arquitetura em camadas dos diagramas, para resolver a incompatibilidade de impedância entre objetos e tabelas:

1. **Apresentação (`InteracaoUsuario`)**:
   - Menus interativos no terminal, feitos com a biblioteca `questionary`.
   - Cinco menus de **CRUD** (um por entidade): listar, cadastrar, atualizar e excluir.
   - Um menu de **Consultas** com as 4 seleções complexas.
2. **Controle (`Controlador`)**: coordena as operações, cria os objetos de domínio e delega a persistência ao adaptador.
3. **Classes de domínio**:
   - `Modalidade` (`idModalidade`, `nome`, `precoMensal`)
   - `Instrutor` (`idInstrutor`, `nome`, `cref`, `idModalidade`)
   - `Aluno` (`idAluno`, `nome`, `cpf`, `dataMatricula`)
   - `MatriculaModalidade` (`idMatriculaModalidade`, `dataAdesao`, `idModalidade`, `idAluno`)
   - `ExameMedico` (`idExame`, `dataAvaliacao`, `situacao`, `idAluno`)
4. **Persistência (`AdaptadorMapaObjetoRelacional`)**:
   - Único ponto do sistema que executa SQL, convertendo objetos em registros e registros em objetos.
   - Conecta ao **MySQL** (`centro_esportivo`) como banco principal, tentando em ordem `PyMySQL`, `mysql-connector` e o cliente de linha de comando `mysql`. Se nenhum funcionar, usa o **SQLite** (`centro_esportivo.db`) como reserva.
   - Cria o banco, as tabelas e os 27 registros iniciais automaticamente quando o banco está vazio.

---

## Seleções Complexas

As 4 consultas estão no script SQL e também no menu **"6 - Consultas"** da aplicação:

| # | Consulta | Técnicas | Resultado com os dados iniciais |
| :- | :--- | :--- | :--- |
| 1 | Ficha de alunos aptos | `INNER JOIN` de 5 tabelas, `WHERE` (exame Apto e mensalidade mínima) | 6 linhas |
| 2 | Auditoria médica: alunos inaptos matriculados | `INNER JOIN` de 5 tabelas, `WHERE situacao = 'Inapto'` | 1 linha (Jeremias Souza) |
| 3 | Receita e alunos por modalidade | `LEFT JOIN`, `GROUP BY`, `COUNT`, `SUM`, `HAVING` | 4 linhas |
| 4 | Alunos em mais de uma modalidade | `INNER JOIN`, `GROUP BY`, `GROUP_CONCAT`, `SUM`, `HAVING > 1` | 2 linhas (Helena e Lucas) |

---

## Script do Banco de Dados (`centro_esportivo.sql`)

O script (MySQL 8) contém:
1. Criação do banco `centro_esportivo` (`utf8mb4`) e das 5 tabelas, com chaves primárias (`AUTO_INCREMENT`), chaves estrangeiras e restrições (`UNIQUE`, `CHECK`, `RESTRICT` e `CASCADE`).
2. Carga de dados (`INSERT`) com 27 registros: 5 modalidades, 5 alunos, 5 instrutores, 5 exames médicos e 7 matrículas.
3. As 4 seleções complexas (`SELECT`).
4. Atualizações (`UPDATE`) e remoções (`DELETE`), com verificação da exclusão em cascata.

Para rodar o script no MySQL:
```bash
mysql -u root -p < "Sistema Centro Esportivo/centro_esportivo.sql"
```

---

## Como Executar a Aplicação

Requisitos: Python 3. O MySQL é opcional (sem ele, a aplicação usa SQLite).

1. Entre na pasta do código:
   ```bash
   cd "Sistema Centro Esportivo"
   ```
2. Crie um ambiente virtual e instale as dependências:
   ```bash
   python -m venv .venv
   ```
   - Windows: `.venv\Scripts\python -m pip install -r requirements.txt`
   - Linux/macOS: `.venv/bin/python -m pip install -r requirements.txt`
3. Execute a aplicação:
   - Windows: `.venv\Scripts\python app.py`
   - Linux/macOS: `.venv/bin/python app.py`

**Conexão com o MySQL:** a aplicação usa o usuário `root` em `localhost` e tenta as senhas `root`, vazia, `1234`, `123456` e `admin`.

**Voltar aos dados iniciais:** apague o arquivo `centro_esportivo.db` (SQLite) ou rode `DROP DATABASE centro_esportivo;` (MySQL). Na próxima execução, o banco é recriado com os 27 registros.
