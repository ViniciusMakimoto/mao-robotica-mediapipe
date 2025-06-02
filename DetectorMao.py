import cv2 
import mediapipe as mp
import serial
import time
import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk

# ========== Inicialização ==========

arduino = None
serial_conectado = False
modo_analogico = False  # Inicia em modo binário

class SimuladorBraco:
    @staticmethod
    def enviar_dedos(dedos):


        if arduino and serial_conectado:
            try:
                if modo_analogico:
                    prefixo = "A"
                else:
                    prefixo = "B"
                string_serial = prefixo + ',' + ','.join(map(str, dedos)) + '\n'
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
valores_abertos = [0, 0, 0, 0, 0]
ultimos_estados = [0, 0, 0, 0, 0]
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

        valores_fechados[:] = [
            abs(pontos[17][0] - pontos[4][0]),
            pontos[5][1] - pontos[8][1],
            pontos[9][1] - pontos[12][1],
            pontos[13][1] - pontos[16][1],
            pontos[17][1] - pontos[20][1]
        ]

        print("Fechamento calibrado:", valores_fechados)
        messagebox.showinfo("Calibração", "Fechamento calibrado com sucesso!")
        calibrado = True

def calibrar_abertura():
    global valores_abertos
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

        valores_abertos[:] = [
            abs(pontos[17][0] - pontos[4][0]),
            pontos[5][1] - pontos[8][1],
            pontos[9][1] - pontos[12][1],
            pontos[13][1] - pontos[16][1],
            pontos[17][1] - pontos[20][1]
        ]

        print("Abertura calibrada:", valores_abertos)
        messagebox.showinfo("Calibração", "Abertura calibrada com sucesso!")

def alternar_modo():
    global modo_analogico
    modo_analogico = not modo_analogico
    btn_modo.config(text=f"Modo: {'Analógico' if modo_analogico else 'Binário'}")

def atualizar_frame():
    global calibrado, ultimos_estados

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
                pontos.append((cx, cy))

        if len(pontos) >= 21:
            dists = [
                abs(pontos[17][0] - pontos[4][0]),
                pontos[5][1] - pontos[8][1],
                pontos[9][1] - pontos[12][1],
                pontos[13][1] - pontos[16][1],
                pontos[17][1] - pontos[20][1]
            ]

            if calibrado:
                if modo_analogico:
                    for i in range(5):
                        aberto = valores_abertos[i]
                        fechado = valores_fechados[i]
                        atual = dists[i]

                        if aberto == fechado:
                            estados[i] = 0.0
                        else:
                            valor = (atual - fechado) / (aberto - fechado)
                            valor = max(0.0, min(1.0, valor))
                            estados[i] = round(valor, 2)
                else:
                    margem_abrir = 15
                    margem_fechar = 5
                    for i, d in enumerate(dists):
                        if ultimos_estados[i] == 0:
                            if d > valores_fechados[i] + margem_abrir:
                                estados[i] = 1
                                ultimos_estados[i] = 1
                            else:
                                estados[i] = 0
                        else:
                            if d < valores_fechados[i] + margem_fechar:
                                estados[i] = 0
                                ultimos_estados[i] = 0
                            else:
                                estados[i] = 1

                mao.enviar_dedos(estados)

    # Exibir vídeo reduzido
    img_reduzida = cv2.resize(img, (320*2, 240*2))
    img_reduzida = cv2.cvtColor(img_reduzida, cv2.COLOR_BGR2RGB)
    imgPIL = Image.fromarray(img_reduzida)
    imgTk = ImageTk.PhotoImage(image=imgPIL)
    lbl_video.imgTk = imgTk
    lbl_video.configure(image=imgTk)

    # Atualiza texto
    texto = ""
    for i in range(5):
        if modo_analogico:
            texto += f"{nomes_dedos[i]}: {estados[i]:.2f}\n"
        else:
            estado = "Aberto" if ultimos_estados[i] == 1 else "Fechado"
            texto += f"{nomes_dedos[i]}: {estado}\n"
    lbl_estado.config(text=texto)

    root.after(10, atualizar_frame)

# ========== Interface Gráfica ==========

root = tk.Tk()
root.title("Controle do Mão Robótico")
root.geometry("1600x850")

lbl_video = tk.Label(root)
lbl_video.pack(pady=5)

btn_iniciar = tk.Button(root, text="Iniciar Comunicação Serial", command=iniciar_serial)
btn_iniciar.pack(pady=5)

btn_calibrar = tk.Button(root, text="Calibrar Fechamento", command=calibrar_fechamento)
btn_calibrar.pack(pady=5)

btn_abertura = tk.Button(root, text="Calibrar Abertura", command=calibrar_abertura)
btn_abertura.pack(pady=5)

btn_modo = tk.Button(root, text="Modo: Binário", command=alternar_modo)
btn_modo.pack(pady=5)

lbl_estado = tk.Label(root, text="Aguardando calibração...", font=("Arial", 11), justify="left")
lbl_estado.pack(pady=10)

btn_sair = tk.Button(root, text="Sair", command=root.quit)
btn_sair.pack(pady=5)

atualizar_frame()
root.mainloop()

cap.release()
cv2.destroyAllWindows()