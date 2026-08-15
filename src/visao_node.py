#!/usr/bin/env python3

import rospy
import cv2
import numpy as np

from sensor_msgs.msg import Image
from cv_bridge import CvBridge
from std_msgs.msg import Float32
from std_msgs.msg import Bool

# VARIÁVEIS GLOBAIS
bridge = CvBridge()

erro_pub = None
found_pub = None
area_pub = None

def callback(msg):

    # Converte a imagem do ROS para OpenCV
    frame = bridge.imgmsg_to_cv2(msg, "bgr8")

    # Detecta o objeto vermelho
    frame, mask, encontrou, erro, area = detect_red_object(frame)

    found_pub.publish(encontrou)

    if encontrou:
        erro_pub.publish(erro)
        area_pub.publish(area)


    # Mostra as imagens
    frame = cv2.resize(frame, (0, 0), fx=0.6, fy=0.6)
    cv2.imshow("Camera", frame)


    cv2.waitKey(1)


# ============================================
# MAIN
# ============================================

def main():

    # Inicializa o nó do ROS
    rospy.init_node("vision_node")
    global erro_pub
    global found_pub
    global area_pub

    # Publishers utilizados pelo control_node
    erro_pub = rospy.Publisher("/vision/error", Float32, queue_size=10)
    found_pub = rospy.Publisher("/vision/found", Bool, queue_size=10)
    area_pub = rospy.Publisher( "/vision/area", Float32, queue_size=10)

    # Subscriber da câmera
    rospy.Subscriber("/camera/rgb/image_raw", Image, callback)

    print("Vision Node iniciado!")

    rospy.spin()

# ============================================
# DETECTA O OBJETO VERMELHO
# ============================================

def detect_red_object(frame):


    # Converte BGR p HSV
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

    # Intervalos de cor para detectar vermelho, pois o vermelho aparece em duas regiões do espaço HSV
    lower_red1 = np.array([0, 120, 70])
    upper_red1 = np.array([10, 255, 255])

    lower_red2 = np.array([170, 120, 70])
    upper_red2 = np.array([180, 255, 255])

    # Cria duas máscaras e as combina
    mask1 = cv2.inRange(hsv, lower_red1, upper_red1)
    mask2 = cv2.inRange(hsv, lower_red2, upper_red2)
    mask = mask1 + mask2

    # Remove pequenos ruídos
    kernel = np.ones((5, 5), np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)

    # Procura o maior objeto vermelho encontrado
    frame, encontrou, erro, area = find_object(frame, mask)

    return frame, mask, encontrou, erro, area

# ============================================
# PROCURA O MAIOR OBJETO VERMELHO
# ============================================

def find_object(frame, mask):

    # -------------------------
    # Contornos
    # -------------------------

    # Procura todos os contornos presentes na máscara
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    # Se nenhum contorno foi encontrado, retorna aviso
    if len(contours) == 0:
        cv2.putText(
            frame,
            "Objeto nao encontrado",
            (20,30),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (0,0,255),
            2
        )

        return frame, False, 0, 0

    # Pega o maior contorno
    largest = max(contours, key=cv2.contourArea)
    area = cv2.contourArea(largest)

    # Ignora pequenos ruídos
    if area < 500:

        cv2.putText(
            frame,
            "Objeto muito pequeno",
            (20,30),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (0,0,255),
            2
        )

        return frame, False, 0, 0

    # Desenha o contorno
    cv2.drawContours(frame, [largest], -1, (0,255,0), 2)


    # ----------------------------
    # Centros do objeto e camera
    # ----------------------------

    # Calcula o centro do objeto
    M = cv2.moments(largest)
    if M["m00"] == 0:
        return frame, False, 0, 0
    cx = int(M["m10"] / M["m00"])
    cy = int(M["m01"] / M["m00"])

    # Desenha um ponto azul no centro do objeto
    cv2.circle(frame, (cx,cy), 6, (255,0,0), -1)

    # Obtem o centro da câmera
    altura, largura = frame.shape[:2]
    centro_x = largura // 2
    centro_y = altura // 2

    # Desenha um ponto amarelo no centro da câmera
    cv2.circle( frame, (centro_x, centro_y), 6, (0,255,255), -1)

    # Desenha linha entre os dois centros
    cv2.line(frame, (centro_x, centro_y), (cx,cy), (255,255,0), 2)

    # Calcula o erro horizontal
    erro = centro_x - cx

    # -------------------------
    # Escreve informações
    # -------------------------

    # Area do objeto:
    cv2.putText(
        frame,
        f"Area: {int(area)}",
        (20,30),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.7,
        (0,0,0),
        2
    )

    # Erro horizontal:
    cv2.putText(
        frame,
        f"Erro: {erro}",
        (20,60),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.7,
        (0,0,0),
        2
    )

    # Centro do objeto:
    cv2.putText(
        frame,
        f"Centro: ({cx}, {cy})",
        (20,90),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.7,
        (0,0,0),
        2
    )

    return frame, True, erro, area

if __name__ == "__main__":
    main()
