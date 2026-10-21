# Sistema de Centro Esportivo

**Instituição:** IFSP – Câmpus Jacareí  
**Curso:** Tecnologia em Análise e Desenvolvimento de Sistemas (ADS)  
**Disciplina:** Banco de Dados 2 (2026)  
**Docente:** Prof. Raul E. S. Castanhari  
**Integrantes:** Camila R. Ribeiro, Helena Vieira e Maria Clara Pastor  

---

## 📌 Sobre o Projeto

Implementação de um **Sistema de Centro Esportivo** com modelagem conceitual (DER), modelo lógico relacional, script completo em **MySQL 8** e uma aplicação interativa no terminal em **Python** estruturada em camadas com Mapeamento Objeto-Relacional (`AdaptadorMapaObjetoRelacional`).

### Entidades e Relacionamentos
- **`Modalidades`**: Esportes oferecidos e preço mensal (`CHECK (preco_mensal >= 0)`).
- **`Instrutores`** (`1:N` com `Modalidades`): Cada instrutor leciona uma modalidade e possui CREF único (`ON DELETE RESTRICT`).
- **`Alunos`**: Cadastro de alunos com CPF único e data de matrícula.
- **`MatriculasModalidades`** (`N:N` associativa entre `Alunos` e `Modalidades`): Guarda a data de adesão (`data_adesao`) e impede matrícula duplicada do mesmo aluno na mesma modalidade (`UNIQUE (id_aluno, id_modalidade)` e `ON DELETE CASCADE`).
- **`ExamesMedicos`** (`1:1` com `Alunos`): Um exame médico por aluno (`Apto` ou `Inapto`, `UNIQUE (id_aluno)` e `ON DELETE CASCADE`).

---

## 🏛 Arquitetura da Aplicação (`app.py`)

A aplicação segue a arquitetura em camadas apresentada nos diagramas do projeto para resolver a incompatibilidade de impedância entre objetos e tabelas:

1. **Camada de Apresentação (`InteracaoUsuario`)**:
   - Menus interativos no terminal feitos com a biblioteca `questionary`.
   - Cinco menus (um para cada entidade) com operações completas de **CRUD** (Listar, Cadastrar, Atualizar e Excluir).
2. **Camada de Controle (`Controlador`)**:
   - Coordena as operações do sistema, instancia os objetos de domínio e delega a persistência ao adaptador.
3. **Classes de Domínio**:
   - `Modalidade` (`idModalidade`, `nome`, `precoMensal`)
   - `Instrutor` (`idInstrutor`, `nome`, `cref`, `idModalidade`)
   - `Aluno` (`idAluno`, `nome`, `cpf`, `dataMatricula`)
   - `MatriculaModalidade` (`idMatriculaModalidade`, `dataAdesao`, `idModalidade`, `idAluno`)
   - `ExameMedico` (`idExame`, `dataAvaliacao`, `situacao`, `idAluno`)
4. **Camada de Persistência (`AdaptadorMapaObjetoRelacional`)**:
   - Único ponto do sistema que executa comandos SQL, convertendo objetos em registros e registros em objetos.
   - Conecta ao **MySQL (`centro_esportivo`)** como banco principal (tentando em ordem: `PyMySQL`, `mysql-connector` e cliente de linha de comando `mysql`) e utiliza **SQLite (`centro_esportivo.db`)** como reserva automática.
   - Cria o banco, as tabelas e os dados iniciais automaticamente caso ainda não existam.

---

## 🗄 Script do Banco de Dados (`centro_esportivo.sql`)

O arquivo `centro_esportivo.sql` (MySQL 8) contempla:
1. Criação do banco `centro_esportivo` (`utf8mb4`) e das 5 tabelas com chaves primárias (`AUTO_INCREMENT`), chaves estrangeiras e restrições de integridade (`UNIQUE`, `CHECK`, `RESTRICT` e `CASCADE`).
2. Carga de dados de exemplo (`INSERT`) com 27 registros (5 modalidades, 5 alunos, 5 instrutores, 5 exames médicos e 7 matrículas).
3. **4 Seleções Complexas (`SELECT`)**:
   - **Consulta 1:** Ficha de alunos aptos (junção de 5 tabelas com filtros `WHERE`).
   - **Consulta 2:** Auditoria médica preventiva de alunos inaptos matriculados (junção de 5 tabelas).
   - **Consulta 3:** Receita mensal e total de alunos por modalidade (`LEFT JOIN`, `GROUP BY`, `COUNT`, `SUM` e `HAVING`).
   - **Consulta 4:** Alunos matriculados em mais de uma modalidade (`INNER JOIN`, `GROUP BY`, `COUNT`, `GROUP_CONCAT`, `SUM` e `HAVING`).
4. Comandos de atualização (`UPDATE`) e remoção (`DELETE`) com verificação de integridade referencial em cascata.

---

## 🚀 Como Executar

1. Instale as dependências do Python:
   ```bash
   pip install -r requirements.txt
   ```

2. Execute a aplicação no terminal:
   ```bash
   python app.py
   ```
   *(No Windows, você também pode executar com `py app.py`)*.
