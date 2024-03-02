# leitor-simulados
Algoritmo em desenvolvimento para fazer a leitura de cartões de respostas de simulados utilizando Visão Computacional e Machine Learning.

## Comandos para construir o container Docker da aplicação:
Siga a documentação oficial para a instalação de *"Docker Engine"* e *"Docker Compose"* e em seguida execute o seguinte comando (a partir da raiz do repositório):
- `docker compose up -d --build --force-recreate`

## Execução do script capaz de detectar macro blocos de informação nas imagens dos cartões de resposta e salva-las em um json:
O `./src/exam_scanner.py` executa dois modelos TensorFlow Lite de detecção de objetos de forma consecutiva e com isso gera imagens renderizadas com as detecções dos objetos em questão, assim como arquivos JSON contendo as coordenadas e níveis de confiança das detecções em cada imagem. 

O script pode ser executado da seguinte forma (a partir de `/workspace` dentro do container):
- `docker exec -it detection_deploy_environment /bin/bash` para iniciar o "bash" do container;
- `python3 ./src/exam_scanner.py --prova <TIPO_DE_PROVA> --input_directory <INPUT_DIR_PATH>` para executar inferências nas imagens presentes em `<INPUT_DIR_PATH>`;
- Outros parâmetros também podem ser ajustados ao executar esse script e podem ser vistos a partir do seguinte comando: `python3 ./src/exam_scanner.py -h`;

## Execução do script que constrói o relatório final a partir das informações presentes no json gerado pelo código anterior.
Já dentro do container docker o script pode ser executado da seguinte maneira:
- `python3 ./src/build_report.py --input_directory <INPUT_DIR>`;
- `INPUT_DIR` deve ser a pasta gerado pelo script anterior que contem o arquivo de texto `report.txt`
- Outros parâmetros também podem ser ajustados ao executar esse script e podem ser vistos a partir do seguinte comando: `python3 ./src/exam_scanner.py -h`;

### Dica.
- O comando `--continue_on_fail` faz com que o código nao encerre em cada erro que encontra em uma detecção.
