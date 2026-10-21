# Sistema Centro Esportivo – Código Fonte

Esta pasta contém o código do trabalho de **Banco de Dados 2** (IFSP Jacareí – ADS).
A documentação completa, com diagramas, está no [README principal](../README.md).

## 📂 Arquivos

- [`app.py`](app.py): aplicação no terminal (Python + `questionary`), com as classes `InteracaoUsuario`, `Controlador`, `AdaptadorMapaObjetoRelacional` e as 5 classes de domínio. Tem CRUD completo das 5 tabelas e um menu com as 4 seleções complexas.
- [`centro_esportivo.sql`](centro_esportivo.sql): script em MySQL 8 com criação do banco e das tabelas, carga de 27 registros (`INSERT`), 4 seleções complexas (`SELECT` com `JOIN`, `GROUP BY` e `HAVING`), atualizações (`UPDATE`) e remoções (`DELETE`).
- [`requirements.txt`](requirements.txt): dependências Python (`questionary` e `pymysql`).

Documentos do trabalho (na raiz do repositório):
- [Relatório técnico](../Relat%C3%B3rio%20-%20Sistema%20Centro%20Esportivo.pdf)
- [Slides da apresentação](../Apresenta%C3%A7%C3%A3o%20de%20slides.pdf)
- [Diagramas](../diagramas)

## 🚀 Como Executar

Dentro desta pasta:

```bash
python -m venv .venv
```

- Windows:
  ```
  .venv\Scripts\python -m pip install -r requirements.txt
  .venv\Scripts\python app.py
  ```
- Linux/macOS:
  ```
  .venv/bin/python -m pip install -r requirements.txt
  .venv/bin/python app.py
  ```

O MySQL é usado se estiver disponível (usuário `root` em `localhost`). Caso contrário, a aplicação usa o SQLite (`centro_esportivo.db`). Para voltar aos dados iniciais, apague o `centro_esportivo.db` ou rode `DROP DATABASE centro_esportivo;` no MySQL.
