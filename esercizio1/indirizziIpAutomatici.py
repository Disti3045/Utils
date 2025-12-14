import re

# Associazione: Nome Rete nel lab.conf -> Numero Host richiesti
DATI_LAN = {
    "C": 7506, # Toscana
    "E": 5346, # Campania
    "A": 3661, # Liguria
    "B": 3314, # Veneto
    "F": 1558, # Calabria
    "H": 938,  # Sicilia
    "D": 752,  # Marche
    "I": 538,  # Sardegna
    "G": 109   # Puglia
}

IP_BASE_STR = "10.42.0.0/16"

# ==============================================================================

def MaskList(size):
    for pw in range(0, 33):
        if 2**pw >= size + 2:
            return 32 - pw
    return 32

def RiscalaIp(ip_input):
    ip = ip_input[:] 
    x = len(ip) - 1
    for i in range(x, -1, -1):
        while ip[i] > 255:
            ip[i] -= 256
            if i - 1 >= 0:
                ip[i-1] += 1
            else:
                break 
    return ip   

def GetLimit(ip_string):
    PART_IP = ip_string.split("/")
    MASK = int(PART_IP[1])
    OTTETTI = [int(x) for x in PART_IP[0].split(".")]
    
    IP_INIZIALE = OTTETTI[:]
    
    for i in range(4):
        ott_precedenti = i * 8 
        if MASK >= ott_precedenti + 8:
            continue
        elif MASK <= ott_precedenti:
            IP_INIZIALE[i] = 0
        else:
            bit_host_qui = 8 - (MASK - ott_precedenti)
            blocco = 2**bit_host_qui
            IP_INIZIALE[i] = (IP_INIZIALE[i] // blocco) * blocco

    dimensione_totale = 2**(32 - MASK)
    IP_FINALE = IP_INIZIALE[:]
    IP_FINALE[3] += (dimensione_totale - 1)
    IP_FINALE = RiscalaIp(IP_FINALE)
    return (tuple(IP_INIZIALE), tuple(IP_FINALE))

def CalcolaProssimaSubnet(IP_PRECEDENTE_END, mask):
    ip_start = list(IP_PRECEDENTE_END)[:]
    ip_start[3] += 1 
    ip_start = RiscalaIp(ip_start)
    
    n_connessioni = 2**(32-mask)
    
    ip_end = ip_start[:]
    ip_end[3] += (n_connessioni - 1)
    ip_end = RiscalaIp(ip_end)
    
    return list(ip_start), list(ip_end)

def ToString(list_ip):
    return f"{list_ip[0]}.{list_ip[1]}.{list_ip[2]}.{list_ip[3]}"

# ==============================================================================

def DividiConPattern(PATH, LIST_PC, LIST_ROUTER):
    try:
        with open(PATH, "r") as file:
            LIST_CONF=file.readlines()
            
            pattern_pc = r"pc\d+\[\d+\]=\S+"
            pattern_router = r"r\d+\[\d+\]=\S+"
            
            for riga in LIST_CONF:
                riga = riga.strip()
                if not riga or riga.startswith("#"): continue
                
                match_pc = re.search(pattern_pc, riga)
                match_router = re.search(pattern_router, riga)
                
                if match_pc:
                    LIST_PC.append(match_pc.group())
                elif match_router:
                    LIST_ROUTER.append(match_router.group())
    except FileNotFoundError:
        print(f"Errore: File {PATH} non trovato.")
        exit()

def SeparaPerRouter(LIST_ROUTER):
    router_dict = {} 
    pattern_id = r"r(\d+)\[\d+\]=(\S+)"
    for riga in LIST_ROUTER:
        match = re.search(pattern_id, riga)
        if match:
            indice = int(match.group(1))
            if indice not in router_dict:
                router_dict[indice] = []
            router_dict[indice].append(match.group(2))
    return router_dict

def EstraiLinkP2P(DICT_ROUTER):
    p2p_links = set()
    for r_id, interfacce in DICT_ROUTER.items():
        for net in interfacce:
            if re.match(r"R\d+R\d+", net):
                p2p_links.add(net)
    
    def natural_keys(text):
        match = re.search(r"R(\d+)R(\d+)", text)
        if match:
            return (int(match.group(1)), int(match.group(2)))
        return (0,0)

    return sorted(list(p2p_links), key=natural_keys)

# ==============================================================================

def AssegnaLanStatiche(DATI_LAN, IP_BASE_START):
    # Ordina: Più grande -> Più piccola
    reti_ordinate = sorted(DATI_LAN.items(), key=lambda item: item[1], reverse=True)
    
    subnet_dict = {} 
    
    fake_end_prev = list(IP_BASE_START)[:]
    fake_end_prev[3] -= 1
    fake_end_prev = RiscalaIp(fake_end_prev)
    last_end = fake_end_prev

    for nome_rete, num_host in reti_ordinate:
        mask = MaskList(num_host)
        start, end = CalcolaProssimaSubnet(last_end, mask)
        subnet_dict[nome_rete] = [tuple(start), mask]
        last_end = end 

    return subnet_dict, last_end

def AssegnaP2P(DICT_SUBNET, LISTA_P2P, LAST_LAN_END):
    current_end = LAST_LAN_END[:]
    
    for link_name in LISTA_P2P:
        start, end = CalcolaProssimaSubnet(current_end, 30)
        DICT_SUBNET[link_name] = [tuple(start), 30]
        current_end = end

    return DICT_SUBNET

def ConfiguraIPRouter(DICT_SUBNET, DICT_ROUTER):
    chiavi_router = sorted(list(DICT_ROUTER.keys()))
    USAGE_COUNTER = {} 

    for r_id in chiavi_router:
        lista_porte = DICT_ROUTER.get(r_id)
        for i in range(len(lista_porte)):
            porta_nome = lista_porte[i]
            
            if porta_nome not in DICT_SUBNET: continue
            
            val_subnet = DICT_SUBNET[porta_nome]
            base_ip = list(val_subnet[0])
            mask = val_subnet[1]
            host_ip = base_ip[:]
            
            match_p2p = re.search(r"R(\d+)R(\d+)", porta_nome)
            
            if match_p2p:
                id_a = int(match_p2p.group(1))
                id_b = int(match_p2p.group(2))
                target_id = min(id_a, id_b)
                
                if r_id == target_id:
                    host_ip[3] += 1
                else:
                    host_ip[3] += 2
            else:
                if porta_nome not in USAGE_COUNTER:
                    USAGE_COUNTER[porta_nome] = 0
                USAGE_COUNTER[porta_nome] += 1
                host_ip[3] += USAGE_COUNTER[porta_nome]

            host_ip = RiscalaIp(host_ip)
            lista_porte[i] = f"{ToString(host_ip)}/{mask}"
    return

# ==============================================================================

def CreaFileStartup(LIST_PC, DICT_SUBNET, IND_CMD, RT_CMD, LISTA_PC_CONF, PATH=""):
    pc_buffer = {}

    for riga in LIST_PC:
        match = re.search(r"(pc\d+)\[(\d+)\]=(\S+)", riga)
        if match:
            nome_pc = match.group(1)
            eth_index = match.group(2)
            nome_rete = match.group(3)
            
            if nome_rete in DICT_SUBNET:
                dati = DICT_SUBNET[nome_rete]
                temp = list(dati[0])
                mask = dati[1]

                # PC: Base + 2 (Assumendo Router .1)
                IP_PC = temp[:]
                IP_PC[3] += 2 
                IP_PC = RiscalaIp(IP_PC)
                str_ip = ToString(IP_PC)
                str_mask = str(mask)
                
                cmd_ip = f"{IND_CMD} {str_ip}/{str_mask} dev eth{eth_index}\n"

                if nome_pc not in pc_buffer:
                    pc_buffer[nome_pc] = []
                pc_buffer[nome_pc].append(cmd_ip)

                if eth_index == "0":
                    IP_GW = temp[:]
                    IP_GW[3] += 1
                    IP_GW = RiscalaIp(IP_GW)
                    str_gw = ToString(IP_GW)
                    cmd_gw = f"{RT_CMD} {str_gw}\n"
                    pc_buffer[nome_pc].append(cmd_gw)

    for nome_pc, comandi in pc_buffer.items():
        nome_file = f"{PATH}{nome_pc}.startup"
        LISTA_PC_CONF.append(nome_file)
        with open(nome_file, "w") as file:
            file.writelines(comandi)

def CreateRouterStartup(DICT_ROUTER, IND_CMD, LISTA_ROUTER_CONF, PATH=""):
    chiavi = sorted(DICT_ROUTER.keys())
    for r_id in chiavi:
        lista_ip = DICT_ROUTER[r_id]
        contenuto_file = ""
        for i in range(len(lista_ip)):
            cidr = lista_ip[i]
            if "/" not in cidr: continue 
            cmd = f"{IND_CMD} {cidr} dev eth{i}\n"
            contenuto_file += cmd
            
        nome_file = f"{PATH}r{r_id}.startup"
        LISTA_ROUTER_CONF.append(nome_file)
        with open(nome_file, "w") as file:
            file.write(contenuto_file)

# ==============================================================================
# main

IND_CMD = "ip addr add"
RT_CMD = "ip route add default via"
LIST_PC = []
LIST_ROUTER = []
LISTA_PC_CONF = []
LISTA_ROUTER_CONF = []

PATH_FILE = "C:/Users/diste/Desktop/esercizio1/lab.conf"
PATH_OUT = "C:/Users/diste/Desktop/esercizio1/"

DividiConPattern(PATH_FILE, LIST_PC, LIST_ROUTER)
DICT_ROUTER = SeparaPerRouter(LIST_ROUTER)

P2P_LIST_SORTED = EstraiLinkP2P(DICT_ROUTER)
print(f"Link P2P trovati: {P2P_LIST_SORTED}")

BASE_LIMITS = GetLimit(IP_BASE_STR)
START_IP_TUPLE = BASE_LIMITS[0]
DICT_SUBNET, LAST_LAN_END = AssegnaLanStatiche(DATI_LAN, list(START_IP_TUPLE))

DICT_SUBNET = AssegnaP2P(DICT_SUBNET, P2P_LIST_SORTED, LAST_LAN_END)

ConfiguraIPRouter(DICT_SUBNET, DICT_ROUTER)

CreaFileStartup(LIST_PC, DICT_SUBNET, IND_CMD, RT_CMD, LISTA_PC_CONF, PATH_OUT)
CreateRouterStartup(DICT_ROUTER, IND_CMD, LISTA_ROUTER_CONF, PATH_OUT)

print("Generazione completata.")
print(f"- {len(LISTA_PC_CONF)} PC configurati")
print(f"- {len(LISTA_ROUTER_CONF)} Router configurati")
print("- Report salvato in report_rete.md")