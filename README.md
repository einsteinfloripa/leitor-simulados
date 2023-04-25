# leitor-simulados
Algoritmo em desenvolvimento para fazer a leitura de cartões de respostas de simulados utilizando Visão Computacional e Machine Learning.

## Comandos para construir o container Docker da aplicação:
Siga a documentação oficial para a instalação de *"Docker Engine"* e *"Docker Compose"* e em seguida execute o seguinte comando (a partir da raiz do repositório):
- `docker compose up -d --build --force-recreate`

## Execução do script capaz de detectar macro blocos de informação nas imagens dos cartões de resposta:
O `./src/run_detection_model.py` executa um modelo TensorFlow Lite de Detection de Objetos e gera imagens renderizadas com as detecções de `cpf_block` e `questions_block`, assim como arquivos JSON contendo as coordenadas e níveis de confiança das detecções em cada imagem. 

O script pode ser executado da seguinte forma (a partir de `/workspace` dentro do container):
- `docker exec -it detection_deploy_environment /bin/bash` para iniciar o "bash" do container;
- `python3 src/run_detection_model.py --input_directory <INPUT_DIR_PATH>` para executar inferências nas imagens presentes em `<INPUT_DIR_PATH>`;
- `python3 src/run_detection_model.py --input_directory <INPUT_DIR_PATH> --crop_objects` para que o script também salve imagens dos recortes de cada objeto detectado;
- Outros parâmetros também podem ser ajustados ao executar esse script e podem ser vistos a partir do seguinte comando: `python3 src/run_detection_model.py -h`;
