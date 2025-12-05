#input lista di connessioni necessarie ->output lista maschere
def MaskList(lista):
    LIST_MASK = []
    for c in lista:
        for pw in range(0, 33):
            if 2**pw>=c+2:
                LIST_MASK.append(32-pw)
                break
            else:
                continue

    return LIST_MASK

#input ip fatto male (elemnti che superano il massimo 255) -> ip riscalato in base 255 correttamente
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

#input ip -> output lista ottetti limite inizio e fine
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

#input lista di mask e tuple di IP(inizio - fine) -> output lista di liste di indirizzi da assegnare
def ListIndirizziOfInterest(MASK_LIST, IP_DOMINIO): 
    RETURN = []
    IP_NEXT = list(IP_DOMINIO[0]) 

    for mask in MASK_LIST:
        IP_START = IP_NEXT[:] 

        n_connessioni = 2**(32-mask)

        IP_END = IP_START[:]
        IP_END[3] += (n_connessioni - 1)
        IP_END = RiscalaIp(IP_END)

        RETURN.append((tuple(IP_START), tuple(IP_END)))

        IP_NEXT = IP_START[:]
        IP_NEXT[3] += n_connessioni
        IP_NEXT = RiscalaIp(IP_NEXT)

    return RETURN

#da lista a stringa, abbastanza ovvio
def ToString(list):
    x = len(list)
    s=""
    for i in range(x):
        s+=str(list[i])
        if i < 3: 
            s += "."
    return s


def CreaFileStartup(LIST_INT, LIST_MASK, IND_CMD, PATH=""):#cartella/cartella/
    for i in range(len(LIST_INT)):
        temp = list(LIST_INT[i][0])
        
        IP_PC = temp[:]
        IP_PC[3] += 1
        IP_PC = RiscalaIp(IP_PC)

        str_ip = ToString(IP_PC)
        str_mask = str(LIST_MASK[i])
        
        s = f"{IND_CMD} {str_ip}/{str_mask} dev eth0\n" #eth da determinare in altra funzione
        with open(f"{PATH}pc{i}.startup", "w") as file:
            file.write(s)
            file.close()

#==============================================================================================
#main
IND_CMD = "ip addr add"
LIST_CON = []

while True:
    val = input("Input numero di connessioni necessarie (0 per terminare): ")
    n = int(val)
    if n <= 0:
        break
    LIST_CON.append(n)

LIST_MASK = MaskList(LIST_CON)


print("Inserisci IP e maschera (es. 153.21.0.0/16): ")
IP_INPUT = str(input())

LIMITI_RETE = GetLimit(IP_INPUT)
LISTA_SUBNET = ListIndirizziOfInterest(LIST_MASK, LIMITI_RETE)

print("\nInserisci il path dove salvare i file (lascia vuoto per cartella corrente): ")
PATH = str(input())

CreaFileStartup(LISTA_SUBNET, LIST_MASK, IND_CMD, PATH)
print(f"Generati {len(LISTA_SUBNET)} file pc[i].startup")