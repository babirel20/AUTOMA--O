# SOBRE O PROJETO

## UTILIZEI GOOGLE ANTIGRAVITY PARA AUXILIAR NO PROJETO.

O intuito deste projeto é uma simulação básica de automação com base em python. O programa retira os dados de um documento (PowerBI,IBGE, Mapa de Empresas e QEdu), retorna para um bloco de notas.


## FUNCIONALIDADES

Na pasta (Gestão de Inventário), criei 4 agentes, cada um com funcionalidades e preparos descritos. As quatro documentações dos agentes foram salvas em markdown para ter melhor desempenho e velocidade de leitrura. Para finalizar, o primeiro agente lê planilhas, segundo pesquisa na web, terceiro analisa os indicadores, quarto escreve planilhas.

## SOBRE A PASTA INDICADORES MUNICIPAIS

Aqui é aonde acontece a mágica, todos os serviços trabalham de forma conjunta e um agente vai repassando ao outro a cada etapa que é concluída. Os agentes trabalham como se fossem um grupo de alunos realizando um trabalho de artes.

## COMO EXECUTAR:

Para executar o script, você precisa utilizar o terminal (ou prompt de comando) e passar o código IBGE do município (que possui 7 dígitos) como argumento para o arquivo principal, que é o agente2_collector.py.

1. Preparar o ambiente (opcional)
Se você quiser ajustar as configurações, copie o arquivo (.env.example)
para um novo arquivo chamado (.env) e altere os valores conforme necessário.

2. Executar o comando
Abra o terminal na pasta do projeto (c:\Users\...\Desktop\AUTOMAÇÃO\indicadores_municipais) e digite o comando abaixo, substituindo <CODIGO_IBGE> pelo código de 7 dígitos da cidade desejada:

```bash
python agente2_collector.py
<CODIGO_IBGE>
```
Exemplo (para a cidade de São Paulo, código 3550308):

```bash
python agente2_collector.py 3550308
```
## O que o script fará:
Ele vai coletar os dados nas 4 fontes configuradas (IBGE, CAGED, Mapa de Empresas e QEdu) e, ao terminar, vai gerar:

- Um arquivo JSON (coleta_3550308.json)
- Uma planilha Excel (coleta_3550308.xlsx)
- Ambos serão salvos na pasta output/.

(Dica: certifique-se de que todas as dependências do projeto estejam instaladas. Pelo código, vi que ele utiliza pacotes como pandas e openpyxl. Caso dê erro de pacote não encontrado, basta instalá-los com pip install -r requirements.txt se houver o arquivo, ou individualmente com pip install pandas openpyxl).
