"""Interface desktop do Pixel Livre. Execute: python app.py."""
import os
from pathlib import Path
import queue
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from PIL import Image, ImageOps, ImageTk

from cleaner import SUPPORTED, clean_image


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title('Pixel Livre • Limpeza de metadados')
        self.geometry('1060x760')
        self.minsize(900, 680)
        self.configure(bg='#f3f6fa')
        self.files = {}
        self.events = queue.Queue()
        self.busy = False
        self.stop = threading.Event()
        self.destination = tk.StringVar()
        self.format = tk.StringVar(value='PNG')
        self.status = tk.StringVar(value='Adicione imagens para começar.')
        self.count = tk.StringVar(value='Nenhuma imagem selecionada')
        self.preview_image = None
        self.controls = []
        self._style()
        self._layout()
        self.protocol('WM_DELETE_WINDOW', self.close)
        self.after(100, self.poll)

    def _style(self):
        style = ttk.Style(self)
        style.theme_use('clam')
        style.configure('.', font=('Segoe UI', 10), background='#f3f6fa', foreground='#172b46')
        style.configure('TButton', padding=(12, 9), background='#e4eaf2', borderwidth=0)
        style.map('TButton', background=[('active', '#d3deec')])
        style.configure('Accent.TButton', background='#2166db', foreground='white', font=('Segoe UI', 11, 'bold'))
        style.map('Accent.TButton', background=[('disabled', '#a9bad6'), ('active', '#1854bb')])
        style.configure('Title.TLabel', font=('Segoe UI', 26, 'bold'))
        style.configure('Muted.TLabel', foreground='#5e6e83')
        style.configure('Heading.TLabel', font=('Segoe UI', 11, 'bold'))
        style.configure('Treeview', rowheight=34, background='white', fieldbackground='white', borderwidth=0)
        style.configure('Treeview.Heading', font=('Segoe UI', 10, 'bold'), padding=8)
        style.configure('Horizontal.TProgressbar', background='#2166db', troughcolor='#e4eaf2', borderwidth=0)

    def button(self, parent, text, command, **kwargs):
        button = ttk.Button(parent, text=text, command=command, **kwargs)
        self.controls.append(button)
        return button

    def _layout(self):
        root = ttk.Frame(self, padding=28)
        root.pack(fill='both', expand=True)
        ttk.Label(root, text='Pixel Livre', style='Title.TLabel').pack(anchor='w')
        ttk.Label(root, text='Suas imagens, sem metadados. Tudo feito localmente no seu computador.', style='Muted.TLabel').pack(anchor='w', pady=(4, 20))
        bar = ttk.Frame(root)
        bar.pack(fill='x')
        self.button(bar, '+ Adicionar imagens', self.add_files).pack(side='left')
        self.button(bar, 'Adicionar pasta', self.add_folder).pack(side='left', padx=8)
        self.button(bar, 'Remover selecionadas', self.remove).pack(side='left')
        ttk.Label(bar, textvariable=self.count, style='Muted.TLabel').pack(side='right')
        content = ttk.Frame(root)
        content.pack(fill='both', expand=True, pady=16)
        content.columnconfigure(0, weight=1)
        content.rowconfigure(0, weight=1)
        listing = ttk.Frame(content)
        listing.grid(row=0, column=0, sticky='nsew')
        self.tree = ttk.Treeview(listing, columns=('name', 'status'), show='headings', selectmode='extended')
        self.tree.heading('name', text='Imagem')
        self.tree.heading('status', text='Resultado')
        self.tree.column('name', width=300, minwidth=180)
        self.tree.column('status', width=170, minwidth=120)
        scroll = ttk.Scrollbar(listing, orient='vertical', command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll.set)
        scroll.pack(side='right', fill='y')
        self.tree.pack(fill='both', expand=True)
        self.tree.bind('<<TreeviewSelect>>', self.preview)
        panel = ttk.Frame(content, width=270, padding=(20, 0, 0, 0))
        panel.grid(row=0, column=1, sticky='ns')
        panel.pack_propagate(False)
        ttk.Label(panel, text='PRÉVIA', style='Heading.TLabel').pack(anchor='w')
        self.preview_label = ttk.Label(panel, text='Selecione uma imagem\npara visualizar.', anchor='center', justify='center')
        self.preview_label.pack(fill='both', expand=True, pady=10)
        self.details = ttk.Label(panel, text='', wraplength=240, style='Muted.TLabel')
        self.details.pack(fill='x')
        output = ttk.LabelFrame(root, text=' Onde salvar as cópias limpas ', padding=14)
        output.pack(fill='x')
        line = ttk.Frame(output)
        line.pack(fill='x')
        entry = ttk.Entry(line, textvariable=self.destination)
        entry.pack(side='left', fill='x', expand=True, padx=(0, 8))
        self.controls.append(entry)
        self.button(line, 'Escolher pasta', self.choose_destination).pack(side='right')
        options = ttk.Frame(output)
        options.pack(fill='x', pady=(12, 0))
        ttk.Label(options, text='Formato:').pack(side='left', padx=(0, 8))
        self.combo = ttk.Combobox(options, textvariable=self.format, values=('PNG', 'JPEG', 'WEBP'), state='readonly', width=9)
        self.combo.pack(side='left')
        ttk.Label(options, text='PNG/WebP: sem perdas • JPEG: fundo branco e recompressão', style='Muted.TLabel').pack(side='left', padx=12)
        ttk.Label(root, text='Remove metadados embutidos, como EXIF, GPS e XMP. Não remove textos ou marcas d’água.\nOs originais são preservados. Perfis de cor são removidos e as cores podem variar.', style='Muted.TLabel').pack(anchor='w', pady=12)
        self.progress = ttk.Progressbar(root, mode='determinate')
        self.progress.pack(fill='x')
        ttk.Label(root, textvariable=self.status, style='Muted.TLabel').pack(anchor='w', pady=(6, 10))
        actions = ttk.Frame(root)
        actions.pack(fill='x')
        self.open_button = ttk.Button(actions, text='Abrir pasta de saída', command=self.open_destination)
        self.open_button.pack(side='left')
        self.cancel_button = ttk.Button(actions, text='Cancelar', command=self.cancel, state='disabled')
        self.cancel_button.pack(side='right', padx=(8, 0))
        self.start_button = ttk.Button(actions, text='Limpar imagens', command=self.start, style='Accent.TButton', state='disabled')
        self.start_button.pack(side='right')

    def add_files(self):
        paths = filedialog.askopenfilenames(title='Escolha suas imagens', filetypes=[('Imagens', '*.png *.jpg *.jpeg *.webp *.bmp *.tif *.tiff')])
        self.add(paths)

    def add_folder(self):
        folder = filedialog.askdirectory(title='Escolha a pasta com imagens')
        if folder:
            try:
                paths = sorted(p for p in Path(folder).iterdir() if p.is_file() and p.suffix.lower() in SUPPORTED)
                self.add(paths)
                if not paths:
                    messagebox.showinfo('Pasta vazia', 'Nenhuma imagem compatível nesta pasta. Subpastas não são incluídas.')
            except OSError as error:
                messagebox.showerror('Não foi possível ler a pasta', str(error))

    def add(self, paths):
        known = set(self.files.values())
        for value in paths:
            path = Path(value).resolve()
            if path not in known:
                row = self.tree.insert('', 'end', values=(path.name, 'Aguardando'))
                self.files[row] = path
                known.add(path)
        if self.files and not self.destination.get():
            self.destination.set(str(next(iter(self.files.values())).parent / 'Imagens limpas'))
        self.refresh()

    def refresh(self):
        self.count.set(f'{len(self.files)} imagem(ns) na lista')
        self.start_button.configure(state='normal' if self.files and not self.busy else 'disabled')

    def remove(self):
        for row in self.tree.selection():
            self.files.pop(row, None)
            self.tree.delete(row)
        self.refresh()
        self.preview()

    def preview(self, _event=None):
        selected = self.tree.selection()
        self.preview_image = None
        self.preview_label.configure(image='', text='Selecione uma imagem\npara visualizar.')
        self.details.configure(text='')
        if not selected:
            return
        path = self.files[selected[0]]
        try:
            with Image.open(path) as source:
                size = source.size
                thumb = ImageOps.exif_transpose(source)
                thumb.thumbnail((240, 180))
                self.preview_image = ImageTk.PhotoImage(thumb.convert('RGBA'))
            self.preview_label.configure(image=self.preview_image, text='')
            result = self.tree.item(selected[0], 'values')[1]
            self.details.configure(text=f'{path.name}\n{size[0]} × {size[1]} px • {path.stat().st_size / 1024:.0f} KB\n{result}')
        except Exception as error:
            self.preview_label.configure(text='Prévia indisponível')
            self.details.configure(text=str(error))

    def choose_destination(self):
        folder = filedialog.askdirectory(title='Onde salvar as imagens limpas?')
        if folder:
            self.destination.set(folder)

    def start(self):
        if self.busy or not self.files:
            return
        if not self.destination.get().strip():
            messagebox.showinfo('Escolha uma pasta', 'Informe a pasta onde deseja salvar as cópias.')
            return
        destination = Path(self.destination.get().strip()).expanduser().resolve()
        if destination.exists() and not destination.is_dir():
            messagebox.showerror('Pasta inválida', 'O destino informado é um arquivo. Escolha uma pasta.')
            return
        self.destination.set(str(destination))
        self.busy = True
        self.stop.clear()
        for control in self.controls:
            control.configure(state='disabled')
        self.combo.configure(state='disabled')
        self.cancel_button.configure(state='normal')
        self.refresh()
        jobs = list(self.files.items())
        self.progress.configure(maximum=len(jobs), value=0)
        for row, path in jobs:
            self.tree.set(row, 'status', 'Aguardando')
        self.status.set('Preparando limpeza…')
        threading.Thread(target=self.work, args=(jobs, destination, self.format.get()), daemon=True).start()

    def work(self, jobs, destination, output_format):
        successes = errors = 0
        for row, path in jobs:
            if self.stop.is_set():
                break
            self.events.put(('working', row, path.name))
            try:
                result = clean_image(path, destination, output_format)
                successes += 1
                self.events.put(('result', row, f'Salva: {result.name}'))
            except Exception as error:
                errors += 1
                self.events.put(('result', row, f'Erro: {error}'))
        self.events.put(('done', successes, errors, len(jobs) - successes - errors))

    def poll(self):
        try:
            while True:
                event = self.events.get_nowait()
                if event[0] == 'working':
                    self.tree.set(event[1], 'status', 'Limpando…')
                    self.status.set(f'Limpando {event[2]}')
                elif event[0] == 'result':
                    self.tree.set(event[1], 'status', event[2])
                    self.progress['value'] += 1
                elif event[0] == 'done':
                    self.busy = False
                    for control in self.controls:
                        control.configure(state='normal')
                    self.combo.configure(state='readonly')
                    self.cancel_button.configure(state='disabled')
                    self.refresh()
                    self.preview()
                    self.status.set(f'Finalizado: {event[1]} salva(s) • {event[2]} erro(s) • {event[3]} não processada(s).')
        except queue.Empty:
            pass
        self.after(100, self.poll)

    def cancel(self):
        self.stop.set()
        self.cancel_button.configure(state='disabled')
        self.status.set('Cancelando após concluir a imagem atual…')

    def open_destination(self):
        folder = Path(self.destination.get()) if self.destination.get() else None
        if folder and folder.is_dir():
            try:
                os.startfile(str(folder))
            except OSError as error:
                messagebox.showerror('Não foi possível abrir a pasta', str(error))
        else:
            messagebox.showinfo('Pasta de saída', 'A pasta será criada ao salvar a primeira imagem.')

    def close(self):
        if self.busy:
            messagebox.showinfo('Limpeza em andamento', 'Cancele ou aguarde a limpeza antes de fechar.')
        else:
            self.destroy()


if __name__ == '__main__':
    App().mainloop()
