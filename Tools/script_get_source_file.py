import os
import tkinter
import pandas as pd
from tkinter import ttk
from tkinter import filedialog
from tkinter import messagebox as mbox


class GUIAutomationJRS:


    def __init__(self):
        self.locale_planbase = ""
        self.locale_planverbas = ""
        self.locale = []
        self.lista_ordenada = []


    def show_animation(self):

        # img = os.getcwd() + '\sistema.png'

        def upload_planilha_base():
            self.locale_planbase = tkinter.filedialog.askopenfilename(title="Selecione a planilha base")

            if self.locale_planbase:
                nome_arquivo = self.locale_planbase.split("/")[-1]
                btn.config(text=nome_arquivo)

        def upload_planilha_verbas():
            self.locale_planverbas = tkinter.filedialog.askopenfilename(title="Selecione a planilha de verbas")
            if self.locale_planverbas:
                nome_arquivo = self.locale_planverbas.split("/")[-1]
                btn2.config(text=nome_arquivo)

        def alterar_cor_button(button, cor_ativa, cor_apagada):
            button.bind("<Enter>", func=lambda e: button.config(foreground=cor_ativa))
            button.bind("<Leave>", func=lambda e: button.config(foreground=cor_apagada))

        def submit():

            if self.locale_planbase:
                self.locale.append(self.locale_planbase)

            if self.locale_planverbas:
                self.locale.append(self.locale_planverbas)


            self.verificar_arquivo(self.locale)

            # self.locale_planbase = ""
            # self.locale_planverbas = ""

            return app.destroy()


        app = tkinter.Tk()
        C = tkinter.Canvas(app, height=300, width=303)
        app.title('Rô-berto')

        filename = tkinter.PhotoImage(file=fr"{os.getcwd()}\Tools\background.png")
        background_label = tkinter.Label(app, image=filename)
        background_label.place(x=0, y=0, relwidth=1, relheight=1)

        # label_pb = tkinter.Label(app, text="Escolha a planilha base")
        # label_pb.place(height=20, width=145, x=90, y=48)

        btn = tkinter.Button(app, text="Escolher Arquivo", font=('Helvetica', '8'), foreground='#28506E',
                             borderwidth=0, background='#FFFFFF', activeforeground='green', activebackground='#FFFFFF', command=upload_planilha_base)
        btn.place(height=20, width=120, x=90, y=132)

        btn2 = tkinter.Button(app, text="Escolher Arquivo", font=('Helvetica', '8'), foreground='#28506E',
                             borderwidth=0, background='#FFFFFF', activeforeground='green', activebackground='#FFFFFF', command=upload_planilha_verbas)
        btn2.place(height=20, width=120, x=90, y=193)

        btn_submit = tkinter.Button(app, text="Enviar", font=('Helvetica', '8'), foreground='#FFFFFF',
                             borderwidth=0, background='#28506E', activeforeground='green', activebackground='#FFFFFF', command=submit)
        btn_submit.place(height=30, width=80, x=110, y=240)

        alterar_cor_button(btn, "red", "#28506E")
        alterar_cor_button(btn2, "red", "#28506E")

        C.pack()
        app.mainloop()


    def exibir_caixa_dialogo(self):
        # Criar uma janela Tkinter para ocultar a caixa de diálogo
        root = tkinter.Tk()
        root.withdraw()
        # Exibir a caixa de diálogo de confirmação
        resposta = mbox.askyesno("Confirmação",
                                 "Foi anexado duas planilhas idênticas. Irei levar em consideração apenas o primeiro anexo.\nDeseja continuar com a operação?")
        # Fechar a janela Tkinter após exibir a caixa de diálogo
        root.destroy()

        return resposta


    @staticmethod
    def _abas(caminho):
        with pd.ExcelFile(caminho) as planilha:
            return set(planilha.sheet_names)

    def _exigir_base(self, caminho):
        # A v3.41 tem a aba CAD; a planilha gerada pelo SAP é reconhecida pela PJE-BD.
        abas = self._abas(caminho)
        if "CAD" not in abas and not ("PJE-BD" in abas and "TBCALCULO" not in abas):
            raise ValueError(f"'{caminho}' não tem a aba CAD nem a PJE-BD")

    def _exigir_verbas(self, caminho):
        if "TBCALCULO" not in self._abas(caminho):
            raise ValueError(f"'{caminho}' não tem a aba TBCALCULO")

    def verificar_arquivo(self, lista):

        # ========= GABARITO ========= #
        # [0]: Somente a planilha base
        # [1]: Somente a planilha verbas
        # [2]: Ambas planilha base/verbas
        # [0/1]: Idênticas

        if len(lista) > 1:
            # Verificar se as planilhas são identicas
            if lista[0] == lista[1] or lista[0].split("/")[-1] == lista[1].split("/")[-1]:
                r = self.exibir_caixa_dialogo()
                print(f'- (Resposta): {r}')
                if not r: exit()
                try:
                    self._exigir_base(lista[0])
                    self.lista_ordenada.append(0)
                    self.lista_ordenada.append(lista[0])
                except Exception:
                    self.lista_ordenada = []
                    try:
                        self._exigir_verbas(lista[0])
                        self.lista_ordenada.append(1)
                        self.lista_ordenada.append(lista[0])
                    except Exception:
                        print(f"- (except): Planilha inválida.")
                        return False
                del lista
                return self.lista_ordenada

            else:

                try:
                    self._exigir_base(lista[0])
                    self._exigir_verbas(lista[1])
                    self.lista_ordenada.append(2)
                    self.lista_ordenada.append(lista[0])
                    self.lista_ordenada.append(lista[1])
                except Exception as e:
                    print(f'- (1ª Except): {e}')
                    self.lista_ordenada = []
                    try:
                        self._exigir_verbas(lista[0])
                        self._exigir_base(lista[1])
                        self.lista_ordenada.append(2)
                        self.lista_ordenada.append(lista[1])
                        self.lista_ordenada.append(lista[0])
                    except Exception as e:
                        print(f'- (2ª Except): {e}')
                        print(f"- (except): Planilha inválida.")
                        print(f'- (Lista)[2ª]: {self.lista_ordenada}')
                        return False

                del lista
                print(f'- (Lista)[Final]: {self.lista_ordenada}')
                return self.lista_ordenada
        else:
            try:
                self._exigir_base(lista[0])
                self.lista_ordenada.append(0)
                self.lista_ordenada.append(lista[0])
            except Exception:
                self.lista_ordenada = []
                try:
                    self._exigir_verbas(lista[0])
                    self.lista_ordenada.append(1)
                    self.lista_ordenada.append(lista[0])
                except Exception:
                    print(f"- (Except): Planilha inválida!")
                    return False
            del lista
            return self.lista_ordenada


if __name__ == "__main__":
    objUI = GUIAutomationJRS()
    objUI.show_animation()