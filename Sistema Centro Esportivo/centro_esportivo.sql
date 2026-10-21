-- =====================================================================
-- BANCO DE DADOS 2 - IFSP JACAREÍ (ADS)
-- PROJETO: SISTEMA DE CENTRO ESPORTIVO
-- SGBD: MySQL 8.0+ / Compatível com MariaDB e SQLite
-- =====================================================================

-- ---------------------------------------------------------------------
-- 1. CRIAÇÃO DA BASE DE DADOS
-- ---------------------------------------------------------------------
SET NAMES utf8mb4;

DROP DATABASE IF EXISTS centro_esportivo;
CREATE DATABASE centro_esportivo
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

USE centro_esportivo;

-- ---------------------------------------------------------------------
-- 2. CRIAÇÃO DAS TABELAS BASE (Sem chaves estrangeiras)
-- ---------------------------------------------------------------------

-- Tabela: Modalidades
-- Representa os esportes oferecidos e seu respectivo preço mensal.
CREATE TABLE Modalidades (
    id_modalidade INT AUTO_INCREMENT PRIMARY KEY,
    nome_modalidade VARCHAR(100) NOT NULL,
    preco_mensal DECIMAL(10, 2) NOT NULL,
    CONSTRAINT chk_preco_positivo CHECK (preco_mensal >= 0)
) ENGINE=InnoDB;

-- Tabela: Alunos
-- Cadastro dos praticantes do centro esportivo com CPF único.
CREATE TABLE Alunos (
    id_aluno INT AUTO_INCREMENT PRIMARY KEY,
    nome_aluno VARCHAR(150) NOT NULL,
    cpf VARCHAR(11) NOT NULL UNIQUE,
    data_matricula DATE NOT NULL
) ENGINE=InnoDB;

-- ---------------------------------------------------------------------
-- 3. CRIAÇÃO DAS TABELAS COM RELACIONAMENTOS (1:N, 1:1, N:N)
-- ---------------------------------------------------------------------

-- Tabela: Instrutores (Relação 1:N com Modalidades)
-- Cada instrutor leciona exatamente 1 modalidade.
-- ON DELETE RESTRICT impede a exclusão de modalidade vinculada a instrutores.
CREATE TABLE Instrutores (
    id_instrutor INT AUTO_INCREMENT PRIMARY KEY,
    nome_instrutor VARCHAR(150) NOT NULL,
    cref VARCHAR(20) NOT NULL UNIQUE,
    id_modalidade INT NOT NULL,
    CONSTRAINT fk_instrutor_modalidade 
        FOREIGN KEY (id_modalidade) REFERENCES Modalidades(id_modalidade)
        ON UPDATE CASCADE 
        ON DELETE RESTRICT
) ENGINE=InnoDB;

-- Tabela: ExamesMedicos (Relação 1:1 com Alunos)
-- Cada aluno realiza exatamente 1 laudo médico ativo.
-- A restrição UNIQUE em id_aluno garante a relação estritamente 1 para 1.
-- ON DELETE CASCADE remove o exame caso o aluno seja excluído.
CREATE TABLE ExamesMedicos (
    id_exame INT AUTO_INCREMENT PRIMARY KEY,
    data_avaliacao DATE NOT NULL,
    situacao ENUM('Apto', 'Inapto') NOT NULL,
    id_aluno INT NOT NULL UNIQUE,
    CONSTRAINT fk_exame_aluno 
        FOREIGN KEY (id_aluno) REFERENCES Alunos(id_aluno)
        ON UPDATE CASCADE 
        ON DELETE CASCADE
) ENGINE=InnoDB;

-- Tabela: MatriculasModalidades (Relação N:N associativa entre Alunos e Modalidades)
-- 1 aluno pode cursar N modalidades; 1 modalidade pode ter N alunos.
-- data_adesao é o atributo próprio do relacionamento.
-- A restrição UNIQUE no par (id_aluno, id_modalidade) impede matrículas duplicadas.
CREATE TABLE MatriculasModalidades (
    id_matricula_modalidade INT AUTO_INCREMENT PRIMARY KEY,
    data_adesao DATE NOT NULL,
    id_modalidade INT NOT NULL,
    id_aluno INT NOT NULL,
    CONSTRAINT fk_matricula_modalidade 
        FOREIGN KEY (id_modalidade) REFERENCES Modalidades(id_modalidade)
        ON UPDATE CASCADE 
        ON DELETE CASCADE,
    CONSTRAINT fk_matricula_aluno 
        FOREIGN KEY (id_aluno) REFERENCES Alunos(id_aluno)
        ON UPDATE CASCADE 
        ON DELETE CASCADE,
    CONSTRAINT uq_aluno_modalidade UNIQUE (id_aluno, id_modalidade)
) ENGINE=InnoDB;

-- ---------------------------------------------------------------------
-- 4. CARGA INICIAL DE DADOS DE EXEMPLO (Volume: 27 Registros)
-- ---------------------------------------------------------------------

-- Inserção de 5 Modalidades
INSERT INTO Modalidades (id_modalidade, nome_modalidade, preco_mensal) VALUES
(1, 'Musculação', 90.00),
(2, 'Crossfit', 150.00),
(3, 'Natação', 150.00),
(4, 'Pilates', 130.00),
(5, 'Boxe', 110.00);

-- Inserção de 5 Alunos
INSERT INTO Alunos (id_aluno, nome_aluno, cpf, data_matricula) VALUES
(1, 'Helena Vieira', '99988877766', '2026-01-10'),
(2, 'Camila Ribeiro', '44433322211', '2026-02-15'),
(3, 'Jeremias Souza', '11122233344', '2026-03-30'),
(4, 'Lucas Silva', '55566677788', '2026-04-10'),
(5, 'Beatriz Lima', '22233344455', '2026-05-15');

-- Inserção de 5 Instrutores
INSERT INTO Instrutores (id_instrutor, nome_instrutor, cref, id_modalidade) VALUES
(1, 'Professora Maria Clara Pastor', 'CREF/SP 11111', 2),
(2, 'Professor Caio Polidoro', 'CREF/SP 22222', 1),
(3, 'Professor Marcelo Costa', 'CREF/SP 33333', 3),
(4, 'Professora Fernanda Souza', 'CREF/SP 44444', 4),
(5, 'Professor Rodrigo Alves', 'CREF/SP 55555', 5);

-- Inserção de 5 Exames Médicos (Relação 1:1)
INSERT INTO ExamesMedicos (id_exame, data_avaliacao, situacao, id_aluno) VALUES
(1, '2026-01-09', 'Apto', 1),
(2, '2026-02-14', 'Apto', 2),
(3, '2026-04-14', 'Inapto', 3),
(4, '2026-04-09', 'Apto', 4),
(5, '2026-05-14', 'Apto', 5);

-- Inserção de 7 Matrículas em Modalidades (Relação N:N)
INSERT INTO MatriculasModalidades (id_matricula_modalidade, data_adesao, id_modalidade, id_aluno) VALUES
(1, '2026-01-10', 1, 1),
(2, '2026-01-20', 2, 1),
(3, '2026-02-15', 2, 2),
(4, '2026-05-15', 3, 3),
(5, '2026-04-10', 1, 4),
(6, '2026-04-12', 3, 4),
(7, '2026-05-15', 4, 5);

-- ---------------------------------------------------------------------
-- 5. SELEÇÕES COMPLEXAS (Consultas Acadêmicas)
-- ---------------------------------------------------------------------

-- Consulta 1: Ficha Geral de Alunos com Exame Apto (Junção de 5 tabelas)
-- Realiza o cruzamento de todas as tabelas para emitir o relatório operacional
-- de alunos com laudo 'Apto' e mensalidade >= R$ 90,00.
SELECT 
    a.nome_aluno AS Aluno,
    a.cpf AS CPF,
    m.nome_modalidade AS Modalidade,
    CONCAT('R$ ', FORMAT(m.preco_mensal, 2, 'pt_BR')) AS Mensalidade,
    i.nome_instrutor AS Instrutor_Responsavel,
    i.cref AS CREF,
    em.situacao AS Situacao_Medica,
    DATE_FORMAT(mm.data_adesao, '%d/%m/%Y') AS Data_Adesao
FROM Alunos a
INNER JOIN MatriculasModalidades mm ON a.id_aluno = mm.id_aluno
INNER JOIN Modalidades m ON mm.id_modalidade = m.id_modalidade
INNER JOIN Instrutores i ON m.id_modalidade = i.id_modalidade
INNER JOIN ExamesMedicos em ON a.id_aluno = em.id_aluno
WHERE em.situacao = 'Apto' 
  AND m.preco_mensal >= 90.00
ORDER BY a.nome_aluno ASC, m.nome_modalidade ASC;

-- Consulta 2: Auditoria Médica Preventiva (Alunos Inaptos Matriculados)
-- Identifica alunos matriculados que estão reprovados no laudo médico,
-- indicando modalidade e instrutor para bloqueio imediato na catraca.
SELECT 
    a.id_aluno,
    a.nome_aluno AS Aluno,
    em.situacao AS Status_Exame,
    DATE_FORMAT(em.data_avaliacao, '%d/%m/%Y') AS Data_Avaliacao_Medica,
    m.nome_modalidade AS Modalidade_Matriculada,
    i.nome_instrutor AS Instrutor_Avisado
FROM Alunos a
INNER JOIN ExamesMedicos em ON a.id_aluno = em.id_aluno
INNER JOIN MatriculasModalidades mm ON a.id_aluno = mm.id_aluno
INNER JOIN Modalidades m ON mm.id_modalidade = m.id_modalidade
INNER JOIN Instrutores i ON m.id_modalidade = i.id_modalidade
WHERE em.situacao = 'Inapto';

-- Consulta 3: Faturamento Estimado e Quantidade de Alunos por Modalidade
-- Utiliza LEFT JOIN, GROUP BY, COUNT, SUM e HAVING para apurar a receita
-- e a quantidade de matriculados em cada esporte ativo.
SELECT 
    m.id_modalidade,
    m.nome_modalidade AS Modalidade,
    i.nome_instrutor AS Instrutor,
    m.preco_mensal AS Valor_Unitario,
    COUNT(mm.id_aluno) AS Total_Alunos_Matriculados,
    SUM(m.preco_mensal) AS Receita_Mensal_Gerada
FROM Modalidades m
LEFT JOIN Instrutores i ON m.id_modalidade = i.id_modalidade
LEFT JOIN MatriculasModalidades mm ON m.id_modalidade = mm.id_modalidade
GROUP BY m.id_modalidade, m.nome_modalidade, i.nome_instrutor, m.preco_mensal
HAVING COUNT(mm.id_aluno) > 0
ORDER BY Receita_Mensal_Gerada DESC;

-- Consulta 4: Alunos Multidisciplinares e Mensalidade Acumulada
-- Localiza alunos matriculados em mais de uma modalidade esportiva,
-- agrupando os nomes dos esportes e calculando a mensalidade total individual.
SELECT 
    a.id_aluno,
    a.nome_aluno AS Aluno,
    COUNT(mm.id_modalidade) AS Qtd_Modalidades,
    GROUP_CONCAT(m.nome_modalidade SEPARATOR ', ') AS Modalidades_Cursadas,
    SUM(m.preco_mensal) AS Mensalidade_Total_Aluno
FROM Alunos a
INNER JOIN MatriculasModalidades mm ON a.id_aluno = mm.id_aluno
INNER JOIN Modalidades m ON mm.id_modalidade = m.id_modalidade
GROUP BY a.id_aluno, a.nome_aluno
HAVING COUNT(mm.id_modalidade) > 1
ORDER BY Mensalidade_Total_Aluno DESC;

-- ---------------------------------------------------------------------
-- 6. ATUALIZAÇÕES (UPDATE) DEMONSTRADAS EM AULA
-- ---------------------------------------------------------------------

-- 1. Reajuste de 10% nas mensalidades superiores a R$ 100,00
UPDATE Modalidades 
SET preco_mensal = ROUND(preco_mensal * 1.10, 2) 
WHERE preco_mensal > 100.00;

-- 2. Liberação médica do aluno Jeremias Souza (id 3)
UPDATE ExamesMedicos 
SET situacao = 'Apto', data_avaliacao = '2026-06-01' 
WHERE id_aluno = 3;

-- 3. Atualização cadastral da aluna Helena Vieira pelo CPF
UPDATE Alunos 
SET nome_aluno = 'Helena Vieira da Silva' 
WHERE cpf = '99988877766';

-- ---------------------------------------------------------------------
-- 7. REMOÇÕES (DELETE) E EFEITO EM CASCATA DEMONSTRADOS EM AULA
-- ---------------------------------------------------------------------

-- 1. Cancelamento da matrícula de Jeremias Souza em Natação
DELETE FROM MatriculasModalidades 
WHERE id_aluno = 3 AND id_modalidade = 3;

-- 2. Remoção da aluna Camila Ribeiro (id 2) e teste de exclusão em cascata
DELETE FROM Alunos 
WHERE id_aluno = 2;

-- 3. Conferência da integridade referencial (as consultas devem retornar vazias)
SELECT * FROM MatriculasModalidades WHERE id_aluno = 2;
SELECT * FROM ExamesMedicos WHERE id_aluno = 2;
