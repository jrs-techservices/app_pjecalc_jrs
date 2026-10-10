import os
import tkinter
from tkinter import ttk
import pandas as pd
from tkinter import filedialog
from tkinter import messagebox as mbox


class GetDadosGUI:


    def __int__(self):
        self.source_file = ""

    def source_file(self):

        def upload_file():
            # source_txt = os.getcwd() + '\source_file.txt'
            # file = open(source_txt, "w")
            conteudo = tkinter.filedialog.askopenfilename(title='Selecione o arquivo .PJC')
            self.source_file = conteudo
            # file.write(conteudo)
            # return file.close(), app.destroy()
            return app.destroy()

        def alterar_cor_button(button, cor_ativa, cor_apagada):
            button.bind("<Enter>", func=lambda e: button.config(foreground=cor_ativa))
            button.bind("<Leave>", func=lambda e: button.config(foreground=cor_apagada))

        img = os.getcwd() + r'\Tools\sistema.png'
        app = tkinter.Tk()

        C = tkinter.Canvas(app, height=200, width=300)
        app.title('Rô-berto')
        filename = tkinter.PhotoImage(file=img)
        background_label = tkinter.Label(app, image=filename)

        background_label.place(x=0, y=0, relwidth=1, relheight=1)
        btn = tkinter.Button(app, text='Clique Aqui', font=('Helvetica', '8'), foreground='#28506E', command=upload_file,
                             borderwidth=0, background='#FFFFFF', activeforeground='green', activebackground='#FFFFFF')
        btn.place(height=20, width=120, x=90, y=110)

        alterar_cor_button(btn, "red", "#28506E")

        C.pack()
        app.mainloop()


class GUIAutomationJRS:


    def __init__(self):

        super(GUIAutomationJRS, self).__init__()
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
                # print("# - Campo 1: ", self.locale_planbase)
                self.locale.append(self.locale_planbase)

            if self.locale_planverbas:
                # print("# - Campo 2: ", self.locale_planverbas)
                self.locale.append(self.locale_planverbas)

            self.verificar_arquivo(self.locale)

            self.locale_planbase = ""
            self.locale_planverbas = ""

            # if self.verificar_arquivo(self.locale):
            return app.destroy()


        app = tkinter.Tk()
        C = tkinter.Canvas(app, height=300, width=303)
        app.title('Rô-berto')

        filename = tkinter.PhotoImage(file=os.getcwd()+r"\Tools\background.png")
        background_label = tkinter.Label(app, image=filename)
        background_label.place(x=0, y=0, relwidth=1, relheight=1)

        # label_pb = tkinter.Label(app, text="Escolha a planilha base")
        # label_pb.place(height=20, width=145, x=90, y=48)

        btn = tkinter.Button(app, text="Escolher Arquivo", font=('Helvetica', '8'), foreground='#28506E',
                             borderwidth=0, background='#FFFFFF', activeforeground='green', activebackground='#FFFFFF', command=upload_planilha_base)
        btn.place(height=20, width=120, x=90, y=132)

        # label_vb = tkinter.Label(app, text="Escolha a planilha de verbas")
        # label_vb.place(height=20, width=145, x=90, y=148)

        btn2 = tkinter.Button(app, text="Escolher Arquivo", font=('Helvetica', '8'), foreground='#28506E',
                             borderwidth=0, background='#FFFFFF', activeforeground='green', activebackground='#FFFFFF', command=upload_planilha_verbas)
        btn2.place(height=20, width=120, x=90, y=193)

        # Estilo do botão
        # style = ttk.Style()
        # style.configure('RoundedButton.TButton', relief='flat', background='#90EE90', foreground='#28506E')
        # style.map('RoundedButton.TButton', background=[('active', 'green')])

        # btn_submit = ttk.Button(app, text="Enviar", style='RoundedButton.TButton', command=submit)
        # btn_submit.place(height=30, width=80, x=110, y=240)

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


    # def verificar_arquivo(self, lista):
    #
    #     print(f"- [VERIFICACAO][PARAMETRO]: {lista}")
    #
    #     # ========= GABARITO ========= #
    #     # [0]: Somente a planilha base
    #     # [1]: Somente a planilha verbas
    #     # [2]: Ambas planilha base/verbas
    #     # [0/1]: Idênticas
    #
    #
    #     if len(lista) > 1:
    #
    #         # Verificar se as planilhas são identicas
    #         if lista[0] == lista[1] or lista[0].split("/")[-1] == lista[1].split("/")[-1]:
    #             r = self.exibir_caixa_dialogo()
    #             if not r:
    #                 exit()
    #             try:
    #                 pd.read_excel(lista[0], sheet_name="CAD")
    #                 self.lista_ordenada.append(0)
    #                 self.lista_ordenada.append(lista[0])
    #             except:
    #                 self.lista_ordenada = []
    #                 try:
    #                     pd.read_excel(lista[0], sheet_name="TBCALCULO")
    #                     self.lista_ordenada.append(1)
    #                     self.lista_ordenada.append(lista[0])
    #                 except:
    #                     print(f"- [Except] - Erro [i2t2]")
    #             del lista
    #             return self.lista_ordenada
    #
    #         else:
    #
    #             try:
    #                 pd.read_excel(lista[0], sheet_name="CAD")
    #             except:
    #                 print(f"- [Except] - Erro [e2t1]")
    #                 try:
    #                     pd.read_excel(lista[1], sheet_name="CAD")
    #                 except:
    #                     print(f"- [Except] - Erro [e2t2]")
    #
    #                 try:
    #                     pd.read_excel(lista[0], sheet_name="TBCALCULO")
    #                 except:
    #                     print(f"- [Except] - Erro [e2t3]")
    #
    #                 self.lista_ordenada.append(2)
    #                 self.lista_ordenada.append(lista[1])
    #                 self.lista_ordenada.append(lista[0])
    #                 del lista
    #                 return self.lista_ordenada
    #
    #             try:
    #                 pd.read_excel(lista[1], sheet_name="TBCALCULO")
    #             except:
    #                 print(f"- [Except] - Erro [e2t4]")
    #
    #             self.lista_ordenada.append(2)
    #             self.lista_ordenada.append(lista[0])
    #             self.lista_ordenada.append(lista[1])
    #             del lista
    #             return self.lista_ordenada
    #     else:
    #
    #         try:
    #             pd.read_excel(lista[0], sheet_name="CAD")
    #             self.lista_ordenada.append(0)
    #             self.lista_ordenada.append(lista[0])
    #         except:
    #             self.lista_ordenada = []
    #             try:
    #                 pd.read_excel(lista[0], sheet_name="TBCALCULO")
    #                 self.lista_ordenada.append(1)
    #                 self.lista_ordenada.append(lista[0])
    #             except:
    #                 print(f"- [Except] - Erro [i2t2]")
    #         del lista
    #         return self.lista_ordenada

    def verificar_arquivo(self, lista):

        if not lista:
            print("- [Erro] Lista de planilhas está vazia.")
            return []

        self.lista_ordenada = []

        if len(lista) == 1:
            return self.verificar_planilha_unica(lista[0])
        elif len(lista) > 1:
            return self.verificar_multiplas_planilhas(lista)
        else:
            print("- [Erro] Condição inesperada.")
            return []

    def verificar_planilha_unica(self, plan):
        print(f"- [PLANILHA]: {plan} {type(plan)}")
        try:
            df = pd.read_excel(plan, sheet_name="CAD")
            if 'Versão' in df.iloc[3, 18]:
                self.lista_ordenada.extend([0, plan])
        except Exception as e:
            print(f"- [Except] - Erro ao abrir 'CAD': {str(e)}")

        try:
            df = pd.read_excel(plan, sheet_name="TBCALCULO")
            if "IIDCALCULO" in df.columns:
                self.lista_ordenada.extend([1, plan])
        except Exception as e:
            print(f"- [Except] - Erro ao abrir 'TBCALCULO': {str(e)}")

        return self.lista_ordenada

    def verificar_multiplas_planilhas(self, lista):
        plan1, plan2 = lista[0], lista[1]
        if plan1 == plan2 or plan1.split("/")[-1] == plan2.split("/")[-1]:
            r = self.exibir_caixa_dialogo()
            if not r:
                exit()
            return self.verificar_planilha_unica(plan1)
        else:
            # self.verificar_planilha_unica(plan1)
            # self.verificar_planilha_unica(plan2)

            try:
                df1 = pd.read_excel(plan1, sheet_name="CAD")
                df2 = pd.read_excel(plan2, sheet_name="TBCALCULO")
                if 'Versão' in df1.iloc[3, 18] and "IIDCALCULO" in df2.columns:
                    self.lista_ordenada.extend([2, plan1, plan2])
                else:
                    print("- [STATUS]: Falha na validação das planilhas (Base/Verbas).")
                    return []
            except Exception as e:
                print(f"- [Except][val.01] - Erro ao abrir 'CAD' and 'TBCALCULO': {str(e)}")
                try:
                    df1 = pd.read_excel(plan2, sheet_name="CAD")
                    df2 = pd.read_excel(plan1, sheet_name="TBCALCULO")
                    if 'Versão' in df1.iloc[3, 18] and "IIDCALCULO" in df2.columns:
                        self.lista_ordenada.extend([2, plan2, plan1])
                    else:
                        print("- [STATUS]: Falha na validação das planilhas (Base/Verbas).")
                        return []
                except Exception as e:
                    print(f"- [Except][val.02] - Erro ao abrir 'CAD' and 'TBCALCULO': {str(e)}")

        return self.lista_ordenada