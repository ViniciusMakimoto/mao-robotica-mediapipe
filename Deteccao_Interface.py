import cv2
import mediapipe as mp
import serial
import time
import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk

# ========== Inicialização ==========

arduino = None  # Só será iniciado após clicar no botão
serial_conectado = False

class SimuladorBraco:
    @staticmethod
    def enviar_dedos(dedos):
        if arduino and serial_conectado:
            try:
                string_serial = ','.join(map(str, dedos)) + '\n'
                arduino.write(string_serial.encode())
            except Exception as e:
                print("Erro ao enviar dados:", e)

mao = SimuladorBraco()

cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
cap.set(3, 640)
cap.set(4, 480)

hands = mp.solutions.hands
Hands = hands.Hands(max_num_hands=1)
mpDraw = mp.solutions.drawing_utils

# ========== Variáveis ==========
calibrado = False
valores_fechados = [0, 0, 0, 0, 0]
nomes_dedos = ["Polegar", "Indicador", "Médio", "Anelar", "Mínimo"]

# ========== Funções ==========
def iniciar_serial():
    global arduino, serial_conectado
    try:
        arduino = serial.Serial('COM5', 9600, timeout=1)
        time.sleep(1)
        serial_conectado = True
        messagebox.showinfo("Sucesso", "Conexão com Arduino iniciada!")
    except Exception as e:
        serial_conectado = False
        messagebox.showerror("Erro", f"Falha ao conectar ao Arduino:\n{e}")

def calibrar_fechamento():
    global calibrado, valores_fechados
    success, img = cap.read()
    if not success:
        print("Não foi possível capturar imagem para calibração.")
        return

    h, w, _ = img.shape
    frameRGB = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    results = Hands.process(frameRGB)
    handPoints = results.multi_hand_landmarks

    if handPoints:
        pontos = []
        for points in handPoints:
            for id, cord in enumerate(points.landmark):
                cx, cy = int(cord.x * w), int(cord.y * h)
                pontos.append((cx, cy))

        if len(pontos) < 21:
            print("Mão não detectada completamente.")
            return

        valores_fechados = [
            abs(pontos[17][0] - pontos[4][0]),
            pontos[5][1] - pontos[8][1],
            pontos[9][1] - pontos[12][1],
            pontos[13][1] - pontos[16][1],
            pontos[17][1] - pontos[20][1]
        ]

        calibrado = True
        print("Calibração concluída:", valores_fechados)

def atualizar_frame():
    global calibrado

    success, img = cap.read()
    if not success:
        root.after(10, atualizar_frame)
        return

    imgRGB = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    results = Hands.process(imgRGB)
    handPoints = results.multi_hand_landmarks
    h, w, _ = img.shape
    pontos = []
    estados = [0, 0, 0, 0, 0]

    if handPoints:
        for points in handPoints:
            mpDraw.draw_landmarks(img, points, hands.HAND_CONNECTIONS)
            for id, cord in enumerate(points.landmark):
                cx, cy = int(cord.x * w), int(cord.y * h)
                cv2.circle(img, (cx, cy), 4, (255, 0, 0), -1)
                pontos.append((cx, cy))

        if len(pontos) >= 21:
            dists = [
                abs(pontos[17][0] - pontos[4][0]),
                pontos[5][1] - pontos[8][1],
                pontos[9][1] - pontos[12][1],
                pontos[13][1] - pontos[16][1],
                pontos[17][1] - pontos[20][1]
            ]

            margem = 10
            if calibrado:
                estados = [
                    1 if d > valores_fechados[i] + margem else 0
                    for i, d in enumerate(dists)
                ]

            mao.enviar_dedos(estados)

    # Reduz o tamanho da imagem da câmera (exibição)
    img_reduzida = cv2.resize(img, (320, 240))
    img_reduzida = cv2.cvtColor(img_reduzida, cv2.COLOR_BGR2RGB)
    imgPIL = Image.fromarray(img_reduzida)
    imgTk = ImageTk.PhotoImage(image=imgPIL)
    lbl_video.imgTk = imgTk
    lbl_video.configure(image=imgTk)

    # Atualiza texto
    texto = ""
    for i in range(5):
        estado = "Aberto" if estados[i] == 1 else "Fechado"
        texto += f"{nomes_dedos[i]}: {estado}\n"
    lbl_estado.config(text=texto)

    root.after(10, atualizar_frame)

# ========== Interface Gráfica ==========
root = tk.Tk()
root.title("Controle do Braço Robótico")
root.geometry("400x450")

lbl_video = tk.Label(root)
lbl_video.pack(pady=5)

btn_iniciar = tk.Button(root, text="Iniciar Comunicação Serial", command=iniciar_serial)
btn_iniciar.pack(pady=5)

btn_calibrar = tk.Button(root, text="Calibrar Fechamento", command=calibrar_fechamento)
btn_calibrar.pack(pady=5)

lbl_estado = tk.Label(root, text="Aguardando calibração...", font=("Arial", 11), justify="left")
lbl_estado.pack(pady=10)

btn_sair = tk.Button(root, text="Sair", command=root.quit)
btn_sair.pack(pady=5)

atualizar_frame()
root.mainloop()

cap.release()
cv2.destroyAllWindows()