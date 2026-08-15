# PB Hover

Projeto desenvolvido no **Núcleo de Robótica Aérea (NRA) da SEMEAR – USP São Carlos**, com o objetivo de implementar o controle autônomo de um hovercraft em ambiente simulado.

O projeto utiliza **ROS Noetic, Gazebo, Python e OpenCV** para integrar simulação, visão computacional e controle de movimento.

## Objetivo

O hovercraft deve identificar um **objeto vermelho** por meio de uma câmera e se movimentar automaticamente em sua direção. A partir da posição do objeto na imagem, o sistema realiza o alinhamento, avança e corrige sua trajetória quando necessário, parando ao atingir uma determinada proximidade.

## Funcionamento

O sistema possui dois nós principais:

* **`visao_node.py`**: recebe as imagens da câmera, realiza a segmentação da cor vermelha utilizando OpenCV e calcula o centro, a área e o erro horizontal do objeto detectado.
* **`control_node.py`**: utiliza essas informações para controlar o hovercraft por meio de comandos de velocidade publicados no tópico `/cmd_vel`.

O funcionamento pode ser resumido em:

```text
Câmera
   ↓
Detecção do objeto vermelho
   ↓
Cálculo da posição e do erro
   ↓
Alinhamento
   ↓
Movimento em direção ao objeto
   ↓
Correção da trajetória
   ↓
Parada ao atingir a proximidade definida
```

Quando o objeto não é encontrado, o hovercraft entra em modo de busca, girando para tentar localizá-lo novamente.

## Tecnologias utilizadas

* **ROS Noetic** — comunicação entre os nós e controle do robô
* **Gazebo** — ambiente de simulação
* **Python** — implementação dos nós
* **OpenCV** — processamento e segmentação das imagens
* **Docker** — configuração e execução do ambiente ROS

## Estrutura principal

```text
pb_hover/
├── launch/
│   ├── gazebo.launch
│   └── hover.launch
├── src/
│   ├── visao_node.py
│   └── control_node.py
├── urdf/
│   └── hover.xacro
├── worlds/
│   └── mundo.world
└── models/
```

## Máquina de Estados

O controle do hovercraft é organizado em quatro estados principais:

```text
                         ┌─────────────────┐
                         │   PROCURANDO    │
                         │                 │
                         │ Gira até        │
                         │ encontrar      │
                         │ o objeto        │
                         └────────┬────────┘
                                  │
                         objeto encontrado
                                  │
                                  ▼
                         ┌─────────────────┐
                         │   ALINHANDO     │
                         │                 │
                         │ Reduz o erro    │
                         │ horizontal      │
                         └────────┬────────┘
                                  │
                         erro <= limite
                                  │
                                  ▼
                         ┌─────────────────┐
                         │    SEGUINDO     │
                         │                 │
                         │ Avança em       │
                         │ direção ao      │
                         │ objeto          │
                         └──────┬─────┬────┘
                                │     │
                    erro grande │     │ área suficiente
                                │     │
                                ▼     ▼
                         ┌──────────┐  ┌─────────────────┐
                         │ALINHANDO │  │     PARADO      │
                         │          │  │                 │
                         │Corrige o │  │ Hovercraft      │
                         │trajeto   │  │ permanece       │
                         └────┬─────┘  │ parado          │
                              │        └────────┬────────┘
                              │                 │
                              └───────┐   objeto perdido
                                      │         │
                                      ▼         ▼
                                  ALINHANDO  PROCURANDO
```

### Resumo dos estados

* **PROCURANDO:** gira até detectar o objeto vermelho.
* **ALINHANDO:** ajusta a orientação para colocar o objeto próximo ao centro da câmera.
* **SEGUINDO:** avança em direção ao objeto enquanto mantém o alinhamento.
* **PARADO:** interrompe o movimento quando o objeto está suficientemente próximo.
* Se o objeto for perdido, o sistema retorna para **PROCURANDO**.
* Se o erro durante o deslocamento ficar muito grande, o sistema retorna para **ALINHANDO**.


## Execução

Com o workspace ROS configurado e compilado:

```bash
source /opt/ros/noetic/setup.bash
source ~/catkin_ws/devel/setup.bash
roslaunch pb_hover hover.launch
```

O launch inicia a simulação no Gazebo e os nós responsáveis pela visão e pelo controle.

## Repositório

https://github.com/MateusSouza48/pb_hover
