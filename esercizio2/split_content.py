import re
import os

def generate_startup_files(input_filename):
    """
    Legge un file di testo contenente configurazioni multiple (formato pc1.startup: ...)
    e genera file singoli per ogni dispositivo.
    """
    
    # Verifica che il file di input esista
    if not os.path.exists(input_filename):
        print(f"Errore: Il file '{input_filename}' non è stato trovato.")
        return

    try:
        with open(input_filename, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        print(f"Errore nella lettura del file: {e}")
        return

    # 1. Pulizia preliminare: Rimuove i tag e spazi extra
    # Questo è necessario perché il testo fornito contiene artefatti
    content_clean = re.sub(r'\\', '', content)  

    # Divide il contenuto in linee
    lines = content_clean.splitlines()

    current_file = None
    current_filename = None

    # Regex per identificare l'inizio di un blocco (es. "r1.startup:")
    # Cerca una stringa alfanumerica che finisce con .startup seguita da due punti
    header_pattern = re.compile(r'^\s*([\w\d]+\.startup)\s*:\s*$')

    print("Inizio elaborazione...")

    for line in lines:
        line = line.strip() # Rimuove spazi a inizio/fine riga
        
        # Salta le righe vuote se non siamo dentro un file, 
        # oppure se sono righe vuote tra un blocco e l'altro
        if not line:
            continue

        # Controlla se la riga è un'intestazione (es. pc1.startup:)
        match = header_pattern.match(line)
        
        if match:
            # Se c'è un file aperto, chiudilo prima di aprirne uno nuovo
            if current_file:
                current_file.close()
                print(f"Creato: {current_filename}")

            # Estrai il nome del nuovo file
            current_filename = match.group(1)
            
            # Apri il nuovo file in modalità scrittura
            try:
                current_file = open(current_filename, 'w', encoding='utf-8')
            except OSError as e:
                print(f"Errore nell'aprire {current_filename}: {e}")
                current_file = None
        else:
            # Se siamo dentro un file aperto, scrivi il contenuto
            if current_file:
                current_file.write(line + '\n')

    # Chiudi l'ultimo file rimasto aperto alla fine del ciclo
    if current_file:
        current_file.close()
        print(f"Creato: {current_filename}")
        
    print("\nOperazione completata!")

# --- CONFIGURAZIONE ---
# Sostituisci 'input_lab.txt' con il nome del file che contiene il testo fornito
INPUT_FILE = 'lab_content.txt' 

if __name__ == "__main__":
    generate_startup_files(INPUT_FILE)