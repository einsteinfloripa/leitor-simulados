# leitor-simulados

### Sumário

1. [Introdução](#introdução)
2. [Requerimentos](#requerimentos)
3. [Setup do programa](#setup-do-programa)  
4. [Uso](#uso)
5. [For Devs](#for-devs)


## Introdução
  Algoritmo em desenvolvimento para fazer a leitura de cartões de respostas de simulados utilizando Visão Computacional e algoritimos tradicionais.
  
## Requerimentos
Antes de começar a instalação, é necessário que os seguintes itens estejam instalados na sua máquina:  
1. `python>=3.10`  
O download para Mac, Windows e Linux pode ser feito no site oficial do Python:
> https://www.python.org/downloads/
2. `Docker`
O guia para a instalação pode ser encontrado em:
> https://docs.docker.com/engine/install/

## Setup do programa
- Clone o repositorio para um diretório local
- Na raiz do repositório use: `docker compose up -d --build --force-recreate`

## Uso
### O script de leitura de simulados pode ser executado da seguinte forma:  
- `docker exec -it detection_deploy_environment /bin/bash` para iniciar o "bash" do container;
- `python3 ./src/exam_scanner.py --prova <TIPO_DE_PROVA> --input_directory <INPUT_DIR_PATH>` para executar inferências nas imagens presentes em `<INPUT_DIR_PATH>`
- Outros parâmetros também podem ser ajustados ao executar esse script e podem ser vistos a partir do seguinte comando: `python3 ./src/exam_scanner.py -h`

### Execução do script que constrói o relatório final a partir das informações presentes no json gerado pelo código anterior.
Já dentro do container docker o script pode ser executado da seguinte maneira:
- `python3 ./src/build_report.py --input_directory <INPUT_DIR>`;
- `INPUT_DIR` deve ser a pasta gerado pelo script anterior que contem o arquivo de texto `report.txt`;
- Outros parâmetros também podem ser ajustados ao executar esse script e podem ser vistos a partir do seguinte comando: `python3 ./src/exam_scanner.py -h`;

### Dicas.
- O comando `--continue_on_fail` faz com que o código nao encerre em cada erro que encontra em uma detecção.

## For Devs
### EFscanAlgo
#### Adicionando pipeline
É possivel implementar novas pipelines de correção das provas dentro do algoritimo de correção convencional, para fazer isso é preciso:  

Criar um arquivo `.py` dentro de `models/EFscanAlgo/first_stage` ou `models/EFscanAlgo/first_stage` dependendo do estagio que se deseja implementar.  

![Screenshot from 2024-08-17 20-35-25](https://github.com/user-attachments/assets/ea6b6770-502c-461e-aa24-7099d381079f)  

O arquivo de pipeline deve conter implementada uma funçao chamada `detect` que será chamada pelo algoritimo principal, para cada imagem a ser analisada, e cuja assinatura deve ser a seguinte:  

![Screenshot from 2024-08-17 20-15-47](https://github.com/user-attachments/assets/a97d4378-cdaa-465f-b409-e6003689c17a)  

Onde:  
- `scanner` é a classe base do algoritimo
- `img` é da classe `core.image.Image` contendo a imagem a ser processada.
- `Detection` é a classe cuja `core.object_detecion.Detection`

#### Init Pipeline
O arquivo de pipeline tambem pode conter uma função chamada `init_pipeline`, que pode ser implementada ou nao, e que será chamada uma vez apenas. A funçao deve ter a seguinte assinatura:

![Screenshot from 2024-08-17 21-03-08](https://github.com/user-attachments/assets/aef297ea-9fc9-4090-a3aa-d54575cd0977)  

Onde:  
- `scanner` é a classe base do algoritimo
- `config` é um dicionario que contem informaçoes:
![Screenshot from 2024-08-17 21-23-06](https://github.com/user-attachments/assets/8f74704f-d95b-452a-a86b-d0290996ba75)  
**Repare que, em `stage` é a real faze em que esta sendo corrigida, e em `model->stage` é o estagio que o modelo supostamente deve corrigir. (É possivel selecionar um modelo de correçao do segundo estagio para corrigir o primeiro estagio, embora isso nao faça muito sentido.)


#### Exemplo de uso:
Essa funçao pode ser usada para iniciar variáveis que serão usadas na funçao `detect` como na pipeline `ef_default_algo` onde é iniciado um modelo yolo que sera futuramente usado para encontrar os cpfs:  
Em `init_pipeline`:  
![Screenshot from 2024-08-17 21-11-10](https://github.com/user-attachments/assets/e46e162d-fe31-41ef-87a0-c2189eb27cd5)  

Em `detect`:  
![Screenshot from 2024-08-17 21-12-54](https://github.com/user-attachments/assets/5414abba-4e9e-4385-a6cd-fae6efa254b6)  


