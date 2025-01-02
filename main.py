import pandas as pd
from facebook_business.api import FacebookAdsApi
from facebook_business.adobjects.serverside.event import Event
from facebook_business.adobjects.serverside.event_request import EventRequest
from facebook_business.adobjects.serverside.user_data import UserData
from facebook_business.adobjects.serverside.custom_data import CustomData
from facebook_business.adobjects.serverside.action_source import ActionSource
import datetime
from tkinter import ttk, filedialog, messagebox
import tkinter as tk
import os
import hashlib
import logging
import json
import queue
import threading
from tqdm import tqdm
from tenacity import retry, stop_after_attempt, wait_exponential

class FieldMappingWindow(tk.Toplevel):
    def __init__(self, parent, columns, required_fields):
        super().__init__(parent)
        self.title("Mapeamento de Campos")
        self.geometry("600x400")
        
        self.columns = columns
        self.required_fields = required_fields
        self.mapping = {}
        
        self.create_widgets()
        
        # Make window modal
        self.transient(parent)
        self.grab_set()

    def create_widgets(self):
        # Instruction label
        ttk.Label(self, text="Mapeie os campos da sua planilha com os campos requeridos:", 
                 wraplength=550).pack(pady=10)

        # Create mapping frame
        mapping_frame = ttk.Frame(self)
        mapping_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # Create mapping entries
        for i, required_field in enumerate(self.required_fields):
            frame = ttk.Frame(mapping_frame)
            frame.pack(fill=tk.X, pady=2)
            
            ttk.Label(frame, text=f"{required_field}:").pack(side=tk.LEFT, padx=5)
            
            combo = ttk.Combobox(frame, values=[""] + self.columns, width=40)
            combo.pack(side=tk.LEFT, padx=5)
            
            # Try to find matching column
            matching_column = self.find_matching_column(required_field)
            if matching_column:
                combo.set(matching_column)
            
            self.mapping[required_field] = combo

        # Buttons
        button_frame = ttk.Frame(self)
        button_frame.pack(fill=tk.X, pady=10)
        
        ttk.Button(button_frame, text="Confirmar", command=self.confirm).pack(side=tk.RIGHT, padx=5)
        ttk.Button(button_frame, text="Cancelar", command=self.cancel).pack(side=tk.RIGHT, padx=5)

    def find_matching_column(self, required_field):
        """Try to find a matching column name"""
        for column in self.columns:
            if column.lower().replace(" ", "_") == required_field.lower():
                return column
        return ""

    def confirm(self):
        # Validate that all required fields are mapped
        unmapped = [field for field, combo in self.mapping.items() 
                   if not combo.get()]
        
        if unmapped:
            messagebox.showerror(
                "Erro", 
                f"Por favor, mapeie todos os campos obrigatórios:\n{', '.join(unmapped)}"
            )
            return
        
        # Store final mapping
        self.final_mapping = {field: combo.get() for field, combo in self.mapping.items()}
        self.destroy()

    def cancel(self):
        self.final_mapping = None
        self.destroy()

class FacebookLeadConverterGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Facebook Lead Converter")
        self.root.geometry("800x600")
        self.message_queue = queue.Queue()
        self.processing = False
        self.config = self.load_config()
        
        # Define required fields
        self.required_fields = [
            'nome', 'email', 'telefone', 'utm_source', 'utm_medium',
            'utm_term', 'utm_campaign', 'utm_content', 'data_registro', 'ip'
        ]
        self.field_mapping = None
        
        self.setup_logging()
        self.create_widgets()
        self.update_status()

    def setup_logging(self):
        log_filename = f'facebook_conversion_log_{datetime.datetime.now().strftime("%Y%m%d_%H%M%S")}.txt'
        logging.basicConfig(
            filename=log_filename,
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )

    def create_widgets(self):
        # Main container
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Credentials Frame
        cred_frame = ttk.LabelFrame(main_frame, text="Credenciais Facebook", padding="5")
        cred_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        
        ttk.Label(cred_frame, text="Access Token:").grid(row=0, column=0, sticky=tk.W)
        self.access_token_var = tk.StringVar(value=self.config.get('access_token', ''))
        self.access_token_entry = ttk.Entry(cred_frame, textvariable=self.access_token_var, width=50)
        self.access_token_entry.grid(row=0, column=1, padx=5, pady=2)
        
        ttk.Label(cred_frame, text="Pixel ID:").grid(row=1, column=0, sticky=tk.W)
        self.pixel_id_var = tk.StringVar(value=self.config.get('pixel_id', ''))
        self.pixel_id_entry = ttk.Entry(cred_frame, textvariable=self.pixel_id_var, width=50)
        self.pixel_id_entry.grid(row=1, column=1, padx=5, pady=2)
        
        self.save_cred_btn = ttk.Button(cred_frame, text="Salvar Credenciais", command=self.save_credentials)
        self.save_cred_btn.grid(row=2, column=0, columnspan=2, pady=5)
        
        # File Selection Frame
        file_frame = ttk.LabelFrame(main_frame, text="Seleção de Arquivo", padding="5")
        file_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        
        self.file_path_var = tk.StringVar()
        self.file_path_entry = ttk.Entry(file_frame, textvariable=self.file_path_var, width=60)
        self.file_path_entry.grid(row=0, column=0, padx=5, pady=5)
        
        self.select_file_btn = ttk.Button(file_frame, text="Selecionar Arquivo", command=self.select_file)
        self.select_file_btn.grid(row=0, column=1, padx=5)
        
        # Progress Frame
        progress_frame = ttk.LabelFrame(main_frame, text="Progresso", padding="5")
        progress_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(progress_frame, variable=self.progress_var, maximum=100)
        self.progress_bar.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), padx=5, pady=5)
        
        # Status Text
        self.status_text = tk.Text(main_frame, height=15, width=70)
        self.status_text.grid(row=3, column=0, columnspan=2, pady=5)
        
        scrollbar = ttk.Scrollbar(main_frame, orient=tk.VERTICAL, command=self.status_text.yview)
        scrollbar.grid(row=3, column=2, sticky=(tk.N, tk.S))
        self.status_text['yscrollcommand'] = scrollbar.set
        
        # Control Buttons
        btn_frame = ttk.Frame(main_frame)
        btn_frame.grid(row=4, column=0, columnspan=2, pady=5)
        
        self.start_btn = ttk.Button(btn_frame, text="Iniciar Processamento", command=self.start_processing)
        self.start_btn.grid(row=0, column=0, padx=5)
        
        self.stop_btn = ttk.Button(btn_frame, text="Parar", command=self.stop_processing, state=tk.DISABLED)
        self.stop_btn.grid(row=0, column=1, padx=5)

    def hash_data(self, data):
        """Convert data to SHA256 hash"""
        if pd.isna(data) or data == '':
            return None
        data = str(data).lower().strip()
        return hashlib.sha256(data.encode('utf-8')).hexdigest()

    def normalize_phone(self, phone):
        """Normalize phone number"""
        if pd.isna(phone) or phone == '':
            return None
        phone = ''.join(filter(str.isdigit, str(phone)))
        if phone and not phone.startswith('55'):
            phone = '55' + phone
        return phone

    def send_to_facebook(self, row, pixel_id, api):
        """Send event to Facebook with retry logic"""
        try:
            # Hash sensitive data
            hashed_email = self.hash_data(row['email'])
            hashed_phone = self.hash_data(self.normalize_phone(row['telefone']))
            
            # Tratar valores nulos dos UTMs
            utm_source = str(row['utm_source']) if not pd.isna(row['utm_source']) else ''
            utm_medium = str(row['utm_medium']) if not pd.isna(row['utm_medium']) else ''
            utm_campaign = str(row['utm_campaign']) if not pd.isna(row['utm_campaign']) else ''
            utm_content = str(row['utm_content']) if not pd.isna(row['utm_content']) else ''
            utm_term = str(row['utm_term']) if not pd.isna(row['utm_term']) else ''
            
            user_data = UserData(
                email=hashed_email,
                phone=hashed_phone,
                client_ip_address=row['ip']
            )

            custom_data = CustomData(
                content_name=utm_campaign if utm_campaign else 'direct'  # Valor padrão se utm_campaign for vazio
            )

            event = Event(
                event_name='Lead',
                event_time=int(row['data_registro'].timestamp()),
                user_data=user_data,
                custom_data=custom_data,
                action_source=ActionSource.WEBSITE,
                event_source_url=f"utm_source={utm_source}&utm_medium={utm_medium}&utm_campaign={utm_campaign}&utm_content={utm_content}&utm_term={utm_term}"
            )

            event_request = EventRequest(
                events=[event],
                pixel_id=pixel_id
            )
            
            event_request.execute()
            return True
            
        except Exception as e:
            self.message_queue.put(f"Erro ao enviar evento para {row['nome']}: {str(e)}")
            raise

    def load_data(self, file_path):
        """Load and validate data file"""
        try:
            if file_path.endswith(('.xlsx', '.xls')):
                df = pd.read_excel(file_path)
            else:
                df = pd.read_csv(file_path)
            
            # Show mapping window
            mapping_window = FieldMappingWindow(self.root, list(df.columns), self.required_fields)
            self.root.wait_window(mapping_window)
            
            if not hasattr(mapping_window, 'final_mapping') or mapping_window.final_mapping is None:
                return None
            
            # Rename columns according to mapping
            self.field_mapping = mapping_window.final_mapping
            df = df.rename(columns={v: k for k, v in self.field_mapping.items()})
            
            return df
            
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao carregar arquivo: {str(e)}")
            return None

    def process_file(self, file_path, access_token, pixel_id):
        try:
            api = FacebookAdsApi.init(access_token=access_token)
            
            self.message_queue.put("Carregando arquivo...")
            df = self.load_data(file_path)
            
            if df is None:
                self.message_queue.put("Falha ao carregar arquivo ou mapeamento cancelado.")
                return
            
            # Convert dates
            df['data_registro'] = pd.to_datetime(df['data_registro'])
            
            total_rows = len(df)
            successful = 0
            failed_rows = []
            
            for index, row in df.iterrows():
                if not self.processing:
                    break
                
                try:
                    if self.send_to_facebook(row, pixel_id, api):
                        successful += 1
                        progress = (index + 1) / total_rows * 100
                        self.progress_var.set(progress)
                        self.message_queue.put(f"Processado com sucesso: {row['nome']}")
                except Exception as e:
                    failed_rows.append(row)
                    self.message_queue.put(f"Falha ao processar {row['nome']}: {str(e)}")
            
            # Export failed rows if any
            if failed_rows:
                self.export_failed_rows(failed_rows)
            
            self.message_queue.put(f"\nProcessamento finalizado!\nTotal processado: {successful}/{total_rows}")
            
        except Exception as e:
            self.message_queue.put(f"Erro durante o processamento: {str(e)}")
        finally:
            self.processing = False
            self.root.after(0, lambda: self.start_btn.config(state=tk.NORMAL))
            self.root.after(0, lambda: self.stop_btn.config(state=tk.DISABLED))

    def export_failed_rows(self, failed_rows):
        """Export failed rows to Excel file"""
        try:
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"failed_rows_{timestamp}.xlsx"
            pd.DataFrame(failed_rows).to_excel(filename, index=False)
            self.message_queue.put(f"Registros com falha exportados para: {filename}")
        except Exception as e:
            self.message_queue.put(f"Erro ao exportar registros com falha: {str(e)}")

    def load_config(self):
        try:
            if os.path.exists('config.json'):
                with open('config.json', 'r') as f:
                    return json.load(f)
        except Exception as e:
            self.message_queue.put(f"Erro ao carregar configuração: {str(e)}")
        return {}

    def save_credentials(self):
        config = {
            'access_token': self.access_token_var.get(),
            'pixel_id': self.pixel_id_var.get()
        }
        try:
            with open('config.json', 'w') as f:
                json.dump(config, f)
            messagebox.showinfo("Sucesso", "Credenciais salvas com sucesso!")
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao salvar credenciais: {str(e)}")

    def select_file(self):
        file_path = filedialog.askopenfilename(
            title="Selecione a planilha",
            filetypes=[
                ("Excel files", "*.xlsx *.xls"),
                ("CSV files", "*.csv"),
                ("All files", "*.*")
            ]
        )
        if file_path:
            self.file_path_var.set(file_path)

    def update_status(self):
        try:
            while True:
                message = self.message_queue.get_nowait()
                self.status_text.insert(tk.END, f"{message}\n")
                self.status_text.see(tk.END)
        except queue.Empty:
            pass
        finally:
            self.root.after(100, self.update_status)

    def start_processing(self):
        if not self.file_path_var.get():
            messagebox.showerror("Erro", "Selecione um arquivo primeiro!")
            return
        
        if not self.access_token_var.get() or not self.pixel_id_var.get():
            messagebox.showerror("Erro", "Preencha as credenciais do Facebook!")
            return
        
        self.processing = True
        self.start_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)
        self.progress_var.set(0)
        
        self.processing_thread = threading.Thread(
            target=self.process_file,
            args=(self.file_path_var.get(), self.access_token_var.get(), self.pixel_id_var.get())
        )
        self.processing_thread.start()

    def stop_processing(self):
        self.processing = False
        self.message_queue.put("Parando processamento...")

def main():
    root = tk.Tk()
    app = FacebookLeadConverterGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()