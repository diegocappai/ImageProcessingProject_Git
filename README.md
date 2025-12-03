Progettare e implementare in Python un programma modulare, che svolga i seguenti compiti principali:

- Acquisizione delle immagini di input e dei dati associati.
- Suddivisione delle immagini in patch e gestione del processo di etichettatura da parte dello specialista.
- Salvataggio strutturato dei risultati.
- Coordinamento e orchestrazione tra i vari moduli.


1) Modulo Input

Funzionalità principali:

Dato un percorso (path) riferito a una singola immagine, il modulo deve caricare:

- l’immagine;
- i dati associati (ID paziente, etichetta presenza/assenza patologia o grado).

Dato un percorso di una cartella che contiene a sua volta le sottocartelle delle singole immagini, il modulo deve:

- iterare sulle sottocartelle;
- caricare progressivamente ogni immagine e i relativi dati associati.

Considerazioni progettuali: occorre tenere conto delle diverse modalità con cui i dati di input possono essere forniti, ad esempio:

- Struttura a cartelle e sottocartelle, una per paziente o per immagine.
- Tutte le immagini in un’unica cartella, accompagnate da un file (es. .json o .csv) contenente le informazioni aggiuntive (ID paziente, etichetta, grado, ecc.).

Il modulo deve gestire almeno due modalità di input (es. cartelle + file indice) e deve essere scritto in modo che sia facile aggiungerne altre in futuro (es. caricamento da database o da archivio remoto).

Output del modulo

Il modulo Input deve inviare al modulo di elaborazione:

- l’immagine caricata;
- l’ID del paziente;
- le informazioni di etichetta associate (patologia o grado).



2) Modulo di elaborazione

Funzionalità principali

- Riceve una singola immagine e la suddivide in “patch” (tasselli).

- Le patch vengono poi presentate allo specialista istopatologo, che assegna un’etichetta (es. presenza/assenza di patologia o grado).


Presentazione all’utente

La presentazione delle patch deve essere gestita da un modulo dedicato, in modo da consentire diversi metodi di interazione.
Si devono prevedere almeno due modalità di presentazione:

- Modalità base (da implementare subito): Le patch vengono presentate una alla volta, in ordine casuale, e l’istopatologo assegna un’etichetta.

- Modalità avanzata (da prevedere, ma si può implementare in seguito): l’intera immagine viene mostrata con la griglia delle patch sovrapposta; l’istopatologo può zoomare e selezionare singole patch da etichettare. Questa modalità può non essere implementata nella prima versione, ma deve poter essere integrata facilmente in futuro.

Funzionalità aggiuntive

- Possibilità di assegnare una etichetta predefinita (ad esempio “non rilevante” o “normale”) a tutte le patch, in modo che lo specialista modifichi solo quelle di interesse.

- Possibilità di ripresentare alcune patch più volte per verificare la consistenza delle etichette assegnate e l’affidabilità della valutazione.

Su questo occorre che ci ragioniamo

3) Modulo Output

Funzionalità principali

Il modulo riceve:

- Le patch e le rispettive etichette dal modulo di elaborazione.

- L’ID del paziente e l’etichetta complessiva del paziente.

Quindi salva i risultati in una o più modalità di output,ad esempio JSON, CSV, oltre alla patch in esame

Il sistema deve essere progettato in modo da poter aggiungere facilmente nuovi formati in seguito (es. database, Excel, ecc.).

Contenuto dell’output

Ogni record salvato deve includere almeno:

- ID paziente
- ID immagine 
- Coordinate o identificativo della patch
- Etichetta assegnata alla patch
- Etichetta assegnata al paziente
- Eventuali informazioni aggiuntive (annotatore, data/ora,...)



4) Modulo Orchestrazione e Interfaccia

Funzionalità principali

Questo modulo collega e coordina il funzionamento dei moduli precedenti, gestendo:

- l’iterazione sulle immagini da processare;
- il passaggio dei dati tra input, elaborazione e output;
- la configurazione del flusso di lavoro (es. tramite file .yaml o .json).

Considerazioni progettuali

Occorre definire chiaramente la responsabilità di ciascun modulo. Occorre che ci ragioniamo. 

Ad esempio:

- Il modulo di input si occupa del caricamento di una singola immagine e dei suoi metadati.
- L’orchestratore gestisce la navigazione dell’intera struttura di cartelle, richiamando il modulo di input per ciascuna immagine trovata e inviandola poi al modulo di elaborazione.

Estendibilità

L’orchestratore deve essere scritto in modo modulare e configurabile, in modo da:

- poter sostituire facilmente un modulo (input, elaborazione o output) con un altro;
- adattarsi a flussi di lavoro diversi (ad esempio diversi formati di input o modalità di annotazione).

----

# NOTE 02.12.2025


## setting iniziali:

Prima di cominciare l'operazione di annotazione, l'esperto deve scegliere le dimensioni delle patch. Esplora il dataset, visualizza una o più immagini  e sceglie la dimensione della patch. Si può pensare ad una interfaccia che mostra l'immagine con in sovrapposizione una griglia che mostra le patch. Un cursore permette di modificare la dimensione delle patch. Un altro cursore (o controllo analogo) permette di effettuare uno zoom. Quando l'esperto ha visionato un numero di immagini ritenuto sufficiente, conferma la dimensione della patch, che varrà per tutte le immagini della sessione.


## logica di etichettatura.

L'etichettatura a livello di singola patch di tutto il dataset può rivelarsi eccessivamente lunga e in concreto non gestibile. Occorre pianificare un percorso alternativo.

- L'esperto ha la _possibilità_ di dividere il dataset in due parti, A e B. la divisione può essere random, manuale dopo ispezione visiva, o definita secondo un certo criterio (es. fanno parte di A le immagini da 1 a n)
- Sulla parte A si procede come detto all'etichettatura della singola patch
- Sulla parte B si assegna globalmente una singola etichetta. Se l'immagine aveva già una sua etichetta globale, il programma può acquisire quella. La parte B non ha una etichetta a livello di patch.

Qual è lo scopo di questo approccio: data l'impossibilità pratica di etichettare a livello di patch l'intero dataset, si può etichettare ogni singola patch del training set, che può essere anche molto piccolo. Per il test set non sono necessarie le etichette a livello di patch, perché siamo interessati a dare una valutazione sullo stato del _paziente_, non della patch. Se il dataset A è costituito da n immagini, con n piccolo, si può utilizzare A come train e B come test. Oppure se i numeri lo consentono si possono realizzare vari training set estraendoli da A

## Gestione dell'input

Spesso in letteratura vengono forniti dataset con immagini già divise in patch, senza informazioni circa l'immagine originale, o con informazioni parziali (per es. [unitopatho](https://github.com/EIDOSLAB/UNITOPATHO) ). E' necessario che il programma possa accettare come input anche immagini in questa forma.


##  statistiche sui dati

Il programma deve fornire statistiche sui dati elaborati (quante imamgini - quante patch - attribuzione alle varie classi, sia a livello di immagine sia di patch

# PROPOSTA TESI

Ragionare su un formato standard per i dataset - analogo a BID per EEG


