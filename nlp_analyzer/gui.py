"""Offline desktop interface built with the standard Tk toolkit."""
from pathlib import Path
import tkinter as tk
import webbrowser
from tkinter import filedialog, messagebox, ttk
from tkinter.scrolledtext import ScrolledText
from .core import AnalysisOptions, analyze
from .reports import render_report
from .identity import AUTHOR_LINES, AUTHOR_EMAIL, AUTHOR_WEBSITE


class AnalyzerWindow:
    def __init__(self, root):
        self.root = root
        self.pending = None
        self.result = None
        self.input_path = None
        root.title('NLP Text Analyzer | ARRahimipour')
        root.geometry('1180x880')
        root.minsize(850, 760)
        root.configure(background='#f2f5f9')
        style = ttk.Style(root)
        style.theme_use('clam')
        style.configure('TFrame', background='#f2f5f9')
        style.configure('TLabel', background='#f2f5f9', foreground='#192637', font=('Arial', 11))
        style.configure('Title.TLabel', font=('Arial', 26, 'bold'))
        style.configure('Metric.TLabel', font=('Arial', 23, 'bold'), foreground='#176b61')
        style.configure('TButton', padding=(12, 8), font=('Arial', 10))
        style.configure('TCheckbutton', background='#f2f5f9')
        style.configure('Treeview', rowheight=29, font=('Arial', 11))
        outer = ttk.Frame(root, padding=24)
        outer.pack(fill='both', expand=True)
        ttk.Label(outer, text='Language, counted.', style='Title.TLabel').pack(anchor='w')
        ttk.Label(outer, text='NLP / SESSION 01  ·  Sentence, word and frequency analysis').pack(anchor='w', pady=(4, 16))
        toolbar = ttk.Frame(outer)
        toolbar.pack(fill='x')
        for label, command in [('Open text', self.open_file), ('Load sample', self.load_sample),
                               ('Export report', self.export), ('Clear', self.clear)]:
            ttk.Button(toolbar, text=label, command=command).pack(side='left', padx=(0, 8))
        self.case = tk.BooleanVar(value=False)
        self.persian = tk.BooleanVar(value=False)
        self.numbers = tk.BooleanVar(value=False)
        options = ttk.Frame(outer)
        options.pack(fill='x', pady=12)
        for label, variable in [('Case sensitive', self.case), ('Persian letter normalization', self.persian),
                                ('Include numbers', self.numbers)]:
            ttk.Checkbutton(options, text=label, variable=variable, command=self.refresh).pack(side='left', padx=(0, 20))
        metrics = ttk.Frame(outer)
        metrics.pack(fill='x', pady=(0, 14))
        self.metric_labels = {}
        for index, name in enumerate(('Sentences', 'Words', 'Unique words', 'Appear once')):
            box = ttk.Frame(metrics, padding=(0, 8))
            box.grid(row=0, column=index, sticky='ew')
            metrics.columnconfigure(index, weight=1)
            value = ttk.Label(box, text='0', style='Metric.TLabel')
            value.pack(anchor='w')
            ttk.Label(box, text=name).pack(anchor='w')
            self.metric_labels[name] = value
        panels = ttk.Panedwindow(outer, orient='horizontal')
        panels.pack(fill='both', expand=True)
        left = ttk.Frame(panels)
        right = ttk.Frame(panels)
        panels.add(left, weight=3)
        panels.add(right, weight=2)
        ttk.Label(left, text='INPUT TEXT · UTF-8').pack(anchor='w', pady=(0, 8))
        self.editor = ScrolledText(left, wrap='word', undo=True, font=('Arial', 12),
                                   relief='flat', padx=14, pady=14, width=44, height=12,
                                   background='white', foreground='#192637', insertbackground='#176b61')
        self.editor.pack(fill='both', expand=True, padx=(0, 14))
        self.editor.bind('<<Modified>>', self.on_modified)
        ttk.Label(right, text='TOP 10 WORDS').pack(anchor='w', pady=(0, 8))
        self.table = ttk.Treeview(right, columns=('rank', 'word', 'count'), show='headings', height=10)
        for column, width in [('rank', 45), ('word', 180), ('count', 65)]:
            self.table.heading(column, text=column.title())
            self.table.column(column, width=width, minwidth=40, anchor='center' if column != 'word' else 'w')
        scrollbar = ttk.Scrollbar(right, orient='vertical', command=self.table.yview)
        self.table.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side='right', fill='y')
        self.table.pack(fill='both', expand=True)
        self.status = ttk.Label(outer, text='', wraplength=1000)
        self.status.pack(fill='x', pady=(14, 4))
        ttk.Label(outer, text='Offline analysis · Numbers are excluded unless Include numbers is selected.',
                  font=('Arial', 9)).pack(anchor='w')
        ttk.Separator(outer, orient='horizontal').pack(fill='x', pady=(12, 8))
        author = ttk.Frame(outer)
        author.pack(fill='x')
        for index, line in enumerate(AUTHOR_LINES[:3]):
            label = ttk.Label(author, text=line, wraplength=780,
                              font=('Arial', 10, 'bold') if index == 0 else ('Arial', 9))
            label.pack(anchor='w')
        for text, url in [(AUTHOR_EMAIL, 'mailto:' + AUTHOR_EMAIL),
                          (AUTHOR_WEBSITE, 'https://' + AUTHOR_WEBSITE)]:
            link = ttk.Label(author, text=text, foreground='#176b61', cursor='hand2',
                             font=('Arial', 9, 'underline'), takefocus=True)
            link.pack(anchor='w')
            link.bind('<Button-1>', lambda event, address=url: webbrowser.open(address))
            link.bind('<Return>', lambda event, address=url: webbrowser.open(address))
        root.bind('<Control-o>', lambda event: self.open_file())
        root.bind('<Control-s>', lambda event: self.export())
        self.refresh()

    def on_modified(self, event=None):
        if self.editor.edit_modified():
            self.editor.edit_modified(False)
            if self.pending is not None:
                self.root.after_cancel(self.pending)
            self.pending = self.root.after(250, self.refresh)

    def refresh(self):
        if self.pending is not None:
            self.root.after_cancel(self.pending)
            self.pending = None
        self.result = analyze(self.editor.get('1.0', 'end-1c'), AnalysisOptions(
            case_sensitive=self.case.get(), persian_normalization=self.persian.get(),
            include_numbers=self.numbers.get()))
        values = [self.result.sentence_count, self.result.word_count,
                  self.result.unique_word_count, self.result.singleton_word_count]
        for label, value in zip(self.metric_labels.values(), values):
            label.configure(text=str(value))
        for item in self.table.get_children():
            self.table.delete(item)
        for index, row in enumerate(self.result.top_words, 1):
            self.table.insert('', 'end', values=(index, row['word'], row['count']))
        status = 'Analysis complete · No word-count limit'
        if self.result.warnings:
            status += ' | ' + self.result.warnings[0]
        self.status.configure(text=status)

    def set_text(self, text):
        self.editor.delete('1.0', 'end')
        self.editor.insert('1.0', text)
        self.refresh()

    def open_file(self):
        path = filedialog.askopenfilename(filetypes=[('Text files', '*.txt'), ('All files', '*')])
        if path:
            try:
                text = Path(path).read_text(encoding='utf-8-sig')
                self.input_path = Path(path).resolve()
                self.set_text(text)
            except (OSError, UnicodeError) as exc:
                messagebox.showerror('Cannot open file', str(exc))

    def load_sample(self):
        path = Path(__file__).resolve().parent.parent / 'examples' / 'english_300.txt'
        try:
            text = path.read_text(encoding='utf-8')
            self.input_path = path.resolve()
            self.set_text(text)
        except OSError as exc:
            messagebox.showerror('Cannot load sample', str(exc))

    def clear(self):
        self.input_path = None
        self.set_text('')

    def export(self):
        self.refresh()
        path = filedialog.asksaveasfilename(defaultextension='.html', initialfile='analysis.html',
            filetypes=[('HTML report', '*.html'), ('JSON report', '*.json'),
                       ('CSV vocabulary', '*.csv'), ('Text report', '*.txt')])
        if path:
            formats = {'.html': 'html', '.json': 'json', '.csv': 'csv', '.txt': 'text'}
            format = formats.get(Path(path).suffix.lower())
            if not format:
                messagebox.showerror('Unsupported format', 'Choose .html, .json, .csv, or .txt.')
                return
            if self.input_path == Path(path).resolve():
                messagebox.showerror('Cannot overwrite input', 'Choose a different output filename.')
                return
            try:
                Path(path).write_text(render_report(self.result, format), encoding='utf-8')
                messagebox.showinfo('Report saved', f'Report saved to:\n{path}')
            except OSError as exc:
                messagebox.showerror('Cannot save report', str(exc))


def launch():
    try:
        root = tk.Tk()
    except tk.TclError as exc:
        raise RuntimeError('Tk could not open a graphical display.') from exc
    AnalyzerWindow(root)
    root.mainloop()
