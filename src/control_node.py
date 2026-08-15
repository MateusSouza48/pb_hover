#!/usr/bin/env python3
import rospy
from std_msgs.msg import Float32
from std_msgs.msg import Bool
from geometry_msgs.msg import Twist



# ============================================
# VARIÁVEIS GLOBAIS
# ============================================

cmd = Twist()

erro = 0.0
area = 0.0
encontrou = False
cmd_pub = None
estado = "PROCURANDO"


# ============================================
# CONSTANTES DE CONTROLE
# ============================================

ERRO_ALINHADO = 5.0
ERRO_REALINHAR = 25.0
VELOCIDADE = 0.25
ROTACAO_PROCURANDO = 0.5
AREA_PARADA = 35000
GANHO_DIRECAO = 0.002


# ============================================
# CALLBACKS
#
# Atualizam as informações recebidas
# do vision_node através dos tópicos ROS.
# ============================================
def error_callback(msg):

    global erro

    erro = msg.data

def area_callback(msg):

    global area

    area = msg.data

def found_callback(msg):

    global encontrou

    encontrou = msg.data


# ============================================
# ESTADO: PROCURANDO
# ============================================

def procurando():

    cmd.linear.x = 0.0

    cmd.angular.z = ROTACAO_PROCURANDO

    cmd_pub.publish(cmd)

# ============================================
# ESTADO: SEGUINDO
# ============================================

def seguindo():

    cmd.linear.x = VELOCIDADE

    cmd.angular.z = 0.0

    cmd_pub.publish(cmd)


# ============================================
# ESTADO: ALINHANDO
# ============================================ 

def alinhando():

    cmd.linear.x = 0.0

    cmd.angular.z = -erro * GANHO_DIRECAO

    # limita a rotação máxima
    if cmd.angular.z > 0.25:
        cmd.angular.z = 0.25

    if cmd.angular.z < -0.25:
        cmd.angular.z = -0.25

    cmd_pub.publish(cmd)

# ============================================
# ESTADO: PARADO
# ============================================

def parar():

    cmd.linear.x = 0.0

    cmd.angular.z = 0.0

    cmd_pub.publish(cmd)


# ============================================
# MAIN
# ============================================

def main():
    
    global cmd_pub
    global estado
    # Inicializa o nó
    rospy.init_node("control_node")

    
    # Publisher que envia velocidade para o robô
    cmd_pub = rospy.Publisher("/cmd_vel", Twist, queue_size=10)

    # Subscribers que recebem informações do vision_node
    rospy.Subscriber("/vision/error", Float32, error_callback)
    rospy.Subscriber("/vision/area", Float32, area_callback)
    rospy.Subscriber("/vision/found", Bool, found_callback)

    # Executa o controle a 10 Hz
    rate = rospy.Rate(10)

    while not rospy.is_shutdown():

        # ==========================================
        # PROCURANDO
        # ==========================================

        if estado == "PROCURANDO":

            if encontrou:

                print("[CONTROL] OBJETO ENCONTRADO!")
                print("[CONTROL] ALINHANDO...")

                estado = "ALINHANDO"
                parar()

            else:

                procurando()


        # ==========================================
        # ALINHANDO
        # ==========================================

        elif estado == "ALINHANDO":

            if encontrou:

                if abs(erro) > ERRO_ALINHADO:

                    alinhando()

                else:

                    print("[CONTROL] ALINHADO!")
                    print("[CONTROL] ERRO:", erro)
                    print("[CONTROL] SEGUINDO...")

                    estado = "SEGUINDO"
                    parar()

            else:

                print("[CONTROL] OBJETO PERDIDO!")
                print("[CONTROL] PROCURANDO...")

                estado = "PROCURANDO"


        # ==========================================
        # SEGUINDO
        # ==========================================

        elif estado == "SEGUINDO":

            # Objeto foi perdido
            if not encontrou:

                print("[CONTROL] OBJETO PERDIDO!")
                print("[CONTROL] PROCURANDO NOVAMENTE...")

                estado = "PROCURANDO"
                parar()

            # Objeto ficou desalinhado
            elif abs(erro) > ERRO_REALINHAR:

                print("[CONTROL] DESALINHOU!")
                print("[CONTROL] ERRO:", erro)
                print("[CONTROL] VOLTANDO A ALINHAR...")

                estado = "ALINHANDO"
                parar()

            # Objeto chegou perto o suficiente
            elif area > AREA_PARADA:

                print("[CONTROL] OBJETO ALCANÇADO!")
                print("[CONTROL] PARADO!")

                estado = "PARADO"
                parar()

            # Tudo certo: continua seguindo reto
            else:

                seguindo()

        # ==========================================
        # PARADO
        # ==========================================

        elif estado == "PARADO":

            # Continua parado enquanto o objeto
            # ainda estiver sendo detectado

            if encontrou:

                parar()

            # Quando o objeto desaparecer,
            # volta a procurar
            else:

                print("[CONTROL] OBJETO SUMIU!")
                print("[CONTROL] PROCURANDO NOVAMENTE...")

                estado = "PROCURANDO"
                procurando()


        rate.sleep()


# ============================================
# INÍCIO DO PROGRAMA
# ============================================    

if __name__ == "__main__":

    try:
        main()

    except rospy.ROSInterruptException:
        pass

    finally:

        if cmd_pub is not None:
            parar()
