
import tkinter as tk
from tkinter import messagebox, ttk

import cache
import sistema_academia as sis

VERDE = "#1b8a3a"
LARANJA = "#c46a00"
CINZA = "#555555"


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Academia BD - Supabase + Redis")
        self.geometry("980x640")
        self.minsize(900, 600)

        self.planos = []
        self.aluno_selecionado = None

        self._montar_cabecalho()
        abas = ttk.Notebook(self)
        abas.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        self.aba_ranking = ttk.Frame(abas)
        self.aba_alunos = ttk.Frame(abas)
        abas.add(self.aba_ranking, text="Ranking (cache Redis)")
        abas.add(self.aba_alunos, text="Alunos")

        self._montar_ranking()
        self._montar_alunos()
        self.after(200, self._carregar_inicial)

    def _montar_cabecalho(self):
        topo = ttk.Frame(self)
        topo.pack(fill="x", padx=10, pady=10)
        ttk.Label(topo, text="Academia BD", font=("Segoe UI", 16, "bold")).pack(side="left")
        self.lbl_redis = ttk.Label(topo, text="Redis: ...", font=("Segoe UI", 10, "bold"))
        self.lbl_redis.pack(side="right")
        self.lbl_checkins = ttk.Label(topo, text="Check-ins hoje (Redis): -")
        self.lbl_checkins.pack(side="right", padx=20)

    def _atualizar_status_redis(self):
        online = cache.redis_online()
        self.lbl_redis.config(text="Redis: ONLINE" if online else "Redis: OFFLINE",
                              foreground=VERDE if online else "#b00020")
        valor = cache.checkins_hoje()
        self.lbl_checkins.config(
            text=f"Check-ins hoje (Redis): {valor if valor is not None else '-'}")

    def _montar_ranking(self):
        barra = ttk.Frame(self.aba_ranking)
        barra.pack(fill="x", padx=10, pady=10)
        ttk.Button(barra, text="Consultar ranking", command=self.consultar_ranking).pack(side="left")
        ttk.Button(barra, text="Limpar cache (Redis)", command=self.limpar_cache).pack(side="left", padx=8)

        self.lbl_origem = tk.Label(self.aba_ranking, text="Clique em 'Consultar ranking'",
                                   font=("Segoe UI", 14, "bold"), fg=CINZA)
        self.lbl_origem.pack(anchor="w", padx=12)
        self.lbl_detalhe = ttk.Label(self.aba_ranking, text="")
        self.lbl_detalhe.pack(anchor="w", padx=12, pady=(0, 6))

        colunas = ("pos", "id", "nome", "plano", "checkins", "ultimo")
        self.tv_ranking = ttk.Treeview(self.aba_ranking, columns=colunas, show="headings", height=18)
        for col, titulo, larg in [("pos", "#", 50), ("id", "ID", 70), ("nome", "Nome", 220),
                                  ("plano", "Plano", 120), ("checkins", "Check-ins", 100),
                                  ("ultimo", "Último check-in", 250)]:
            self.tv_ranking.heading(col, text=titulo)
            self.tv_ranking.column(col, width=larg, anchor="w")
        self.tv_ranking.pack(fill="both", expand=True, padx=10, pady=10)

    def consultar_ranking(self):
        self.lbl_origem.config(text="Consultando...", fg=CINZA)
        self.update_idletasks()
        try:
            r = sis.ranking(50)
        except Exception as e:
            messagebox.showerror("Erro", f"Falha ao consultar o ranking:\n{e}")
            return

        if r["origem"] == "REDIS":
            self.lbl_origem.config(text=f"Origem: REDIS (cache)  •  {r['ms']} ms", fg=VERDE)
            detalhe = f"Dados vindos da memória do Redis. Expira em {r['ttl']}s."
        else:
            self.lbl_origem.config(text=f"Origem: SUPABASE (banco)  •  {r['ms']} ms", fg=LARANJA)
            detalhe = ("Consulta executada na VIEW do Supabase e salva no Redis."
                       if r["redis_ok"] else "Redis offline: consulta feita direto no Supabase.")
        self.lbl_detalhe.config(text=detalhe)

        self.tv_ranking.delete(*self.tv_ranking.get_children())
        for i, (aid, nome, plano, total, ultimo) in enumerate(r["dados"], start=1):
            self.tv_ranking.insert("", "end", values=(i, aid, nome, plano or "-", total,
                                                      str(ultimo)[:19] if ultimo else "-"))
        self._atualizar_status_redis()

    def limpar_cache(self):
        sis._invalidar_ranking()
        self.lbl_origem.config(text="Cache limpo. A próxima consulta vai ao Supabase.", fg=CINZA)
        self.lbl_detalhe.config(text="")

    def _montar_alunos(self):
        busca = ttk.Frame(self.aba_alunos)
        busca.pack(fill="x", padx=10, pady=10)
        ttk.Label(busca, text="Buscar:").pack(side="left")
        self.var_busca = tk.StringVar()
        ent = ttk.Entry(busca, textvariable=self.var_busca, width=30)
        ent.pack(side="left", padx=6)
        ent.bind("<Return>", lambda e: self.carregar_alunos())
        ttk.Button(busca, text="Pesquisar", command=self.carregar_alunos).pack(side="left")

        colunas = ("id", "nome", "email", "plano", "ativo")
        self.tv_alunos = ttk.Treeview(self.aba_alunos, columns=colunas, show="headings", height=11)
        for col, titulo, larg in [("id", "ID", 70), ("nome", "Nome", 220), ("email", "E-mail", 260),
                                  ("plano", "Plano", 120), ("ativo", "Ativo", 70)]:
            self.tv_alunos.heading(col, text=titulo)
            self.tv_alunos.column(col, width=larg, anchor="w")
        self.tv_alunos.pack(fill="both", expand=True, padx=10)
        self.tv_alunos.bind("<<TreeviewSelect>>", self._ao_selecionar)

        form = ttk.LabelFrame(self.aba_alunos, text="Dados do aluno")
        form.pack(fill="x", padx=10, pady=10)
        self.var_nome, self.var_email, self.var_plano = tk.StringVar(), tk.StringVar(), tk.StringVar()
        ttk.Label(form, text="Nome").grid(row=0, column=0, padx=6, pady=6, sticky="e")
        ttk.Entry(form, textvariable=self.var_nome, width=30).grid(row=0, column=1, padx=6)
        ttk.Label(form, text="E-mail").grid(row=0, column=2, padx=6, sticky="e")
        ttk.Entry(form, textvariable=self.var_email, width=30).grid(row=0, column=3, padx=6)
        ttk.Label(form, text="Plano").grid(row=1, column=0, padx=6, pady=6, sticky="e")
        self.cb_plano = ttk.Combobox(form, textvariable=self.var_plano, state="readonly", width=28)
        self.cb_plano.grid(row=1, column=1, padx=6)

        botoes = ttk.Frame(self.aba_alunos)
        botoes.pack(fill="x", padx=10, pady=(0, 10))
        ttk.Button(botoes, text="Cadastrar", command=self.cadastrar).pack(side="left")
        ttk.Button(botoes, text="Atualizar", command=self.atualizar).pack(side="left", padx=6)
        ttk.Button(botoes, text="Excluir", command=self.excluir).pack(side="left")
        ttk.Button(botoes, text="Registrar check-in (Procedure)", command=self.checkin).pack(side="left", padx=18)
        ttk.Button(botoes, text="Total de check-ins (Function)", command=self.total).pack(side="left")
        ttk.Button(botoes, text="Limpar campos", command=self.limpar_form).pack(side="right")

    def _carregar_inicial(self):
        try:
            self.planos = sis.listar_planos()
            self.cb_plano["values"] = [p[1] for p in self.planos]
            if self.planos:
                self.cb_plano.current(0)
            self.carregar_alunos()
        except Exception as e:
            messagebox.showerror(
                "Erro de conexão",
                f"Não foi possível acessar o Supabase.\n\n{e}\n\n"
                "Confira o .env e se rodou: python src/criar_banco.py")
        self._atualizar_status_redis()

    def carregar_alunos(self):
        try:
            linhas = sis.listar_alunos(self.var_busca.get().strip())
        except Exception as e:
            messagebox.showerror("Erro", str(e))
            return
        self.tv_alunos.delete(*self.tv_alunos.get_children())
        for aid, nome, email, plano, ativo in linhas:
            self.tv_alunos.insert("", "end", values=(aid, nome, email, plano, "Sim" if ativo else "Não"))

    def _ao_selecionar(self, _):
        sel = self.tv_alunos.selection()
        if not sel:
            return
        aid, nome, email, plano, _ativo = self.tv_alunos.item(sel[0], "values")
        self.aluno_selecionado = int(aid)
        self.var_nome.set(nome)
        self.var_email.set(email)
        self.var_plano.set(plano)

    def limpar_form(self):
        self.aluno_selecionado = None
        self.var_nome.set("")
        self.var_email.set("")
        if self.planos:
            self.cb_plano.current(0)
        self.tv_alunos.selection_remove(self.tv_alunos.selection())

    def _plano_id(self):
        for pid, nome, _ in self.planos:
            if nome == self.var_plano.get():
                return pid
        return None

    def _dados_validos(self):
        nome, email = self.var_nome.get().strip(), self.var_email.get().strip()
        if not nome or "@" not in email:
            messagebox.showwarning("Atenção", "Informe um nome e um e-mail válidos.")
            return None
        return nome, email, self._plano_id()

    def _exigir_selecao(self):
        if self.aluno_selecionado is None:
            messagebox.showinfo("Atenção", "Selecione um aluno na tabela.")
            return False
        return True

    def cadastrar(self):
        dados = self._dados_validos()
        if not dados:
            return
        try:
            sis.cadastrar_aluno(*dados)
        except Exception as e:
            messagebox.showerror("Erro", f"Não foi possível cadastrar:\n{e}")
            return
        messagebox.showinfo("Sucesso", "Aluno cadastrado. O cache do ranking foi invalidado no Redis.")
        self.limpar_form()
        self.carregar_alunos()

    def atualizar(self):
        if not self._exigir_selecao():
            return
        dados = self._dados_validos()
        if not dados:
            return
        try:
            sis.atualizar_aluno(self.aluno_selecionado, *dados)
        except Exception as e:
            messagebox.showerror("Erro", f"Não foi possível atualizar:\n{e}")
            return
        self.carregar_alunos()

    def excluir(self):
        if not self._exigir_selecao():
            return
        if not messagebox.askyesno("Confirmar", "Excluir este aluno e seus check-ins?"):
            return
        try:
            sis.excluir_aluno(self.aluno_selecionado)
        except Exception as e:
            messagebox.showerror("Erro", str(e))
            return
        self.limpar_form()
        self.carregar_alunos()

    def checkin(self):
        if not self._exigir_selecao():
            return
        try:
            sis.registrar_checkin(self.aluno_selecionado)
        except Exception as e:
            messagebox.showerror("Erro", str(e))
            return
        self._atualizar_status_redis()
        messagebox.showinfo("Check-in", "Check-in registrado pela Procedure sp_registrar_checkin.")

    def total(self):
        if not self._exigir_selecao():
            return
        try:
            n = sis.total_checkins(self.aluno_selecionado)
        except Exception as e:
            messagebox.showerror("Erro", str(e))
            return
        messagebox.showinfo("Total", f"Total de check-ins (Function fn_total_checkins): {n}")


if __name__ == "__main__":
    App().mainloop()
