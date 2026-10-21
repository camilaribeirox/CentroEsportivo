# Sistema de Gestão de Centro Esportivo

**Instituição:** IFSP – Câmpus Jacareí  
**Curso:** Tecnologia em Análise e Desenvolvimento de Sistemas (ADS)  
**Disciplina:** Banco de Dados 2  
**Docente:** Prof. Raul E. S. Castanhari  

---

## 📌 Sobre o Projeto

Implementação de um **Sistema de Centro Esportivo / Academia** utilizando **MySQL 8** e aplicação de terminal em **Python** estruturada em camadas com Mapeamento Objeto-Relacional (`AdaptadorMapaObjetoRelacional`).

### Entidades e Relacionamentos
- **`Modalidades`**: Esportes oferecidos e preço mensal.
- **`Instrutores`** (`1:N` com `Modalidades`): Cada instrutor leciona uma modalidade e possui CREF único (`ON DELETE RESTRICT`).
- **`Alunos`**: Cadastro de alunos com CPF único e data de matrícula.
- **`MatriculasModalidades`** (`N:N` associativa entre `Alunos` e `Modalidades`): Guarda a data de adesão e impede matrícula duplicada do mesmo aluno na mesma modalidade (`ON DELETE CASCADE`).
- **`ExamesMedicos`** (`1:1` com `Alunos`): Um exame médico por aluno (`Apto` ou `Inapto`, `UNIQUE (id_aluno)`, `ON DELETE CASCADE`).

---

## 📐 Diagramas do Projeto

### 1. Diagrama Entidade-Relacionamento (DER)
![DER](diagramas/der.png)

### 2. Modelo Relacional (Tabelas e Chaves)
![Modelo Relacional](diagramas/modelo_relacional.png)

### 3. Diagrama de Classes de Domínio
![Diagrama de Classes de Domínio](diagramas/diagrama_classes_dominio.png)

### 4. Arquitetura e Persistência ORM
![Diagrama de Classes e Arquitetura](diagramas/diagrama_classes_arquitetura.png)

---

## 📂 Estrutura dos Arquivos

- [`app.py`](app.py): Aplicação interativa no terminal (Python + `questionary`) com as classes `InteracaoUsuario`, `Controlador`, `AdaptadorMapaObjetoRelacional` e as 5 classes de domínio.
- [`centro_esportivo.sql`](centro_esportivo.sql): Script completo em MySQL 8 contendo criação do banco, tabelas, chaves, carga de dados (`INSERT`), 4 seleções complexas (`SELECT` com `JOIN`, `GROUP BY`, `HAVING`), atualizações (`UPDATE`) e remoções (`DELETE`).
- [`BD2 - Centro Esportivo.pdf`](BD2%20-%20Centro%20Esportivo.pdf): Apresentação de slides do projeto.
- [`Relatório Trabalho - Sistema Centro Esportivo.pdf`](Relatório%20Trabalho%20-%20Sistema%20Centro%20Esportivo.pdf): Relatório técnico do trabalho.
- [`requirements.txt`](requirements.txt): Dependências Python (`questionary` e `pymysql`).

---

## 🚀 Como Executar

1. Instale as dependências:
   ```bash
   pip install -r requirements.txt
   ```
2. Execute a aplicação no terminal:
   ```bash
   python app.py
   ```
   *(No Windows, você também pode usar `py app.py`)*.
