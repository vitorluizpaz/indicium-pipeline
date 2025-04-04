
# Desafio Indicium Tech

Este projeto utiliza várias ferramentas para orquestrar uma pipeline de dados usando o Meltano e Apache Airflow.

## Estrutura do Projeto
1. **Pré-requisitos**  
   Feita a instalação do python, todas as ferramentas podem ser instaladas em qualquer ordem exceto meltano e pipx, o pipx deve **NECESSARIAMENTE** estar instalado quando a instalação do meltano for feita. Se o meltano não for instalado através do pipx isso pode gerar alguns conflitos.
   - [Git](https://git-scm.com/downloads)
   - [Python 3.12.0](https://www.python.org/downloads/release/python-3120/)  
   - [Docker](https://www.docker.com/)  
   - [Pipx](https://pipx.pypa.io/stable/installation/)  
   - [Meltano](https://docs.meltano.com/guide/installation-guide)  
   - [Airflow (pip install apache-airflow)](https://airflow.apache.org/docs/apache-airflow/stable/installation/index.html)


2. **Arquivos Necessários para Rodar o Projeto**  
   Para começar utilize o seguinte comando para clonar o repositório:
   ```bash
   git clone https://github.com/vitorluizpaz/indicium-pipeline.git
   ```
3. **Gerenciamento de Containers com Docker**  
   Foi fornecido um arquivo `docker-compose` para gerenciar a criação dos containers `postgres-source` e `postgres-target`, ambos com serviços de banco de dados utilizando a imagem do PostgreSQL. Navegue através do terminal até a pasta raiz do projeto e execute:
   ```bash
   docker-compose up -d
   ```

   Agora vamos carregar `postgres-source` com o arquivo `northwind.sql` fornecido:
   ```bash
   docker cp "./files/northwind.sql" postgres_source:/var/lib/northwind.sql
   ```  
   ```bash
   docker exec -it postgres_source psql -U source_user -d northwind -f /var/lib/northwind.sql
   ```

4. **Instalação do Meltano**  
   Com o terminal dentro da pasta meltano executaremos:
   ```bash
   meltano init .
   ```
   
5. **Criação de Extratores e Loaders**  
   - Dentro da pasta meltano há um arquivo meltano.yml, ele guarda todos os plugins que utilizaremos 
   - **Substitua** o seu arquivo meltano.yml pelo arquivo meltano.yml presente na pasta files.  

      **ATENÇÃO**: Para criar os extratores e loaders, utilizamos os templates fornecidos na [documentação oficial do Meltano Labs](https://github.com/meltanolabs).  
   - **Extratores**:
      - Criamos um extrator para o arquivo CSV fornecido (`tap-csv`).
      - Criamos extratores para cada tabela do banco de dados (`tap-postgres` e extratores do tipo `tap-postgres-{table}`). **Exceção**: Tabelas vazias, que geram erro quando usadas com `tap-postgres`.  
         **Nota**: A necessidade de um extrator por tabela se dá pelo fato de que o `tap-postgres` por padrão extrai **todas as tabelas**. Para evitar isso, criamos extratores específicos para cada tabela utilizando o parâmetro `select` (parte do passo 1 do desafio).
      
   - **Loaders**:
      - Criamos um loader para o arquivo CSV fornecido (`target-csv`).
      - Criamos um loader único para as tabelas fornecidas (`target-db-csv`). A separação se fez necessária devido aos diferentes padrões de diretório nos arquivos.
      - Agora, com os arquivos no formato CSV, criamos um novo extrator (`tap-csv2`) para passar as tabelas e o arquivo CSV localizado no sistema local (parte do passo 2 do desafio).
      - Para carregar os dados extraídos, criamos o `target-postgres` (parte do passo 2).  

6. **Configuração do Banco de Dados do Airflow**  
   A seguir, inicializaremos o banco de dados do Airflow com o comando:
   ```bash
   airflow db init
   ```

7. **Configuração do Meltano com Airflow**  
   O arquivo `meltano.yml` foi editado para adicionar o Airflow como um plugin orquestrador.  
   Após isso, utilizamos os comandos (Necessariamente com o terminal dentro da pasta meltano):  
   - Atualiza as dependencias
   ```bash
   meltano lock --update --all
   ```
   - Instala os plugins
   ```bash
   meltano install
   ```

8. **Configuração das DAGs**  
   Vamos configurar o Airflow para direcionar a leitura das DAGs.  
   Navegue através do terminal até a pasta dags contida dentro de indicium-pipeline/meltano/orchestrate/dags, obtenha o caminho absoluto utilizando pwd no terminal.
   No arquivo `airflow.cfg (geralmente dentro da pasta ~/airflow)`, alteramos a linha `dags_folder` para:
   ```
   dags_folder = {CAMINHO_ABSOLUTO_DA_PASTA_DAGS}
   ```

9. **Execução das DAGs**  
   **Para executar o airflow e conseguirmos rodar as DAGs que dependem do meltano, precisamos estar com o terminal dentro da pasta meltano que está contida no nosso projeto.**  
   Agora podemos rodar o Airflow com o comando:
   ```
   airflow standalone
   ```
  
   Após iniciar o Airflow, podemos disparar as DAGs usando os comandos (elas serão disparadas com a data atual):
   ```bash
   airflow dags unpause {dag_id}
   ```
   Após testarmos, para evitar que ela fique rodando podemos usar:
   ```bash
   airflow dags pause {dag_id}
   ```

10. **Testando os Passos da Pipeline**  
   - Primeiro, rodamos **pipeline_step1** para verificar o primeiro passo.
   - Em seguida, rodamos **pipeline_step2** para verificar o segundo passo.
   - Se as DAGs rodaram com sucesso, as pastas `csv` e `postgres` deverão surgir no diretório **indicium-pipeline/data** e um relatório de sucesso para cada DAG deve surgir no terminal.

11. **Rodando a Pipeline Completa**  
    Agora você pode disparar a DAG pipeline_full para executar a pipeline completa. Sugiro testar com uma data do passado e outras, para que essas dags não reaproveitem os arquivos gerados pelos steps 1 e 2:  

      ```bash
      airflow dags trigger {nome_da_dag} -e {EXECUTION_DATE=YYYY-MM-DD}
      ```

12. **Exportando a Query**  
    Após rodar a pipeline, podemos rodar uma consulta SQL para garantir o funcionamento:
    ```bash
    docker exec -it postgres_target bash
    ```

    ```bash
    psql -U target_user -d targetdb -c "COPY (SELECT o.order_id, od.product_id, od.unit_price, od.quantity, od.discount FROM orders o JOIN order_details od ON o.order_id = od.order_id) TO '/var/lib/postgresql/data/final_file.csv' WITH CSV HEADER"
    ```

    Por fim, saímos do contêiner e copiamos o arquivo gerado para o sistema local (utilize pwd no terminal dentro da pasta indicium-pipeline/data/final para obter o **caminho absoluto**):
    ```bash
    docker cp postgres_target:/var/lib/postgresql/data/final_file.csv {CAMINHO_ABSOLUTO}
    ```