
# Backlog

## 1. Modello dati di annotazione (`ANNOTATION`)

### Obiettivo

Definire una struttura dati persistente che consenta di:

* tracciare la suddivisione in patch
* registrare le etichette assegnate
* salvare annotazioni e note
* riprendere una sessione interrotta
* supportare sia immagine singola sia cartella di patch già esistenti
* visualizzare lo stato delle patch sull’immagine principale, quando disponibile

### Scelta progettuale

* usare **JSON** come formato principale di serializzazione
* prevedere una struttura composta da:

  * metadati del caso/sessione
  * configurazione di patching
  * lista delle patch
  * stato di avanzamento
  * storico annotazioni opzionale
  
In subordine tabella PANDAS - ma sarebbe meglio usare questo JSON . 

Si può adottare questa struttura JSON occupandosi di riempire per ora solo le parti principali ma lasciando la struttura intera per il futuro. Predisporre anche funzioni di conversione


### Struttura minima proposta di `ANNOTATION`

```json
{
  "schema_version": "1.0",
  "case_id": "case_001",
  "source_type": "whole_image | patch_folder",
  "source_path": "path/to/source",
  "created_at": "2026-03-17T10:00:00Z",
  "updated_at": "2026-03-17T10:20:00Z",
  "image_metadata": {
    "width": 10000,
    "height": 8000,
    "channels": 3,
    "microns_per_pixel": null
  },
  "patching_config": {
    "patch_size": 256,
    "patch_shape": "square",
    "overlap": 0,
    "generated_by_program": true
  },
  "sampling_config": {
    "roi_list": [],
    "sampling_percentage": 20,
    "sampling_strategy": "random | grid | stratified"
  },
  "progress": {
    "total_patches": 1200,
    "eligible_patches": 400,
    "shown_patches": 120,
    "labeled_patches": 118,
    "skipped_patches": 2,
    "completed": false
  },
  "patches": [
    {
      "patch_id": "p_000001",
      "file_name": null,
      "x": 0,
      "y": 0,
      "width": 256,
      "height": 256,
      "roi_id": "roi_01",
      "selected_for_review": true,
      "shown_to_user": true,
      "status": "labeled | skipped | pending",
      "label": "tumor",
      "annotation_text": "presenza di necrosi",
      "user_id": "medico_01",
      "reviewed_at": "2026-03-17T10:15:00Z"
    }
  ]
}
```

### Task

* definire schema JSON formale
* versionare lo schema (`schema_version`)
* introdurre campi obbligatori e opzionali
* prevedere compatibilità futura con nuovi campi
* definire mapping opzionale verso DataFrame pandas per analisi/report

### Criteri di accettazione

* una sessione può essere salvata e riaperta senza perdita di informazioni
* è possibile sapere in ogni momento:

  * quante patch esistono
  * quante sono state mostrate
  * quante etichettate
  * quali restano da valutare

---

## 2. Flusso unico di caricamento input

### Obiettivo

Gestire con un unico processo due casi:

1. input = immagine istologica singola
2. input = cartella con patch già suddivise

### Decisione funzionale

Introdurre un **flusso unico**, con una fase iniziale di normalizzazione dell’input:

* se input è immagine singola:

  * il programma genera la griglia delle patch
  * salva coordinate e metadati
* se input è cartella di patch:

  * il programma indicizza i file patch
  * se le coordinate esistono, le salva
  * se non esistono, lavora comunque in modalità “patch-only”

### Modalità supportate

* **mode = full-image-backed**

  * esiste immagine originale
  * esistono coordinate patch
  * possibile ricostruzione overlay sulla immagine principale
* **mode = patch-folder-with-coordinates**

  * esistono patch separate con coordinate note
  * possibile overlay se si conosce il canvas originale
* **mode = patch-folder-without-coordinates**

  * esistono solo patch isolate
  * non è possibile ricostruire la posizione sull’immagine originale
  * annotazione comunque possibile

### Task

* rilevare automaticamente il tipo di input
* creare un adapter unico per entrambi i casi
* separare logica di input da logica di annotazione
* definire fallback quando mancano coordinate

### Criteri di accettazione

* l’utente può aprire sia immagine singola sia cartella patch senza cambiare workflow
* il programma gestisce in modo esplicito il caso “coordinate non disponibili”
* il sistema non tenta overlay sull’immagine originale se le coordinate non esistono

---

## 3. Creazione e ripresa sessione

### Obiettivo

Consentire la continuità del lavoro tra sessioni diverse.

### Flusso desiderato

#### Caso A: immagine mai aperta

* utente apre nuova immagine o cartella patch
* il programma crea `ANNOTATION`
* utente seleziona ROI da esaminare
* utente imposta percentuale di patch da valutare
* il programma costruisce l’insieme di patch candidate
* il programma mostra le patch una per volta
* l’utente assegna etichetta e annotazioni
* il programma salva immediatamente in `ANNOTATION`

#### Caso B: immagine già aperta

* utente apre sorgente già associata a un `ANNOTATION`
* il programma ricarica stato, patch già viste e già etichettate
* utente può ridefinire ROI e percentuale, secondo regole da stabilire
* il programma seleziona solo le patch ancora non valutate
* il programma riprende dal punto interrotto

### Task

* implementare autosave ad ogni annotazione
* associare in modo robusto `ANNOTATION` alla sorgente
* gestire riapertura di sessione incompleta
* gestire sessione completata ma riapribile per revisione
* introdurre lock o warning se due utenti aprono lo stesso caso contemporaneamente

### Criteri di accettazione

* chiudendo il programma non si perde il lavoro
* riaprendo il caso si riparte correttamente
* le patch già annotate non vengono riproposte, salvo richiesta di revisione

---

## 4. Definizione ROI e campionamento patch

### Obiettivo

Permettere al medico di limitare l’analisi a regioni di interesse e a una percentuale di patch.

### Requisiti

* selezione manuale di una o più ROI
* definizione percentuale di patch da esaminare
* selezione delle patch solo dentro ROI
* esclusione automatica delle patch fuori ROI
* possibilità di cambiare strategia di campionamento

### Strategie possibili

* casuale
* sequenziale
* griglia uniforme
* stratificata per ROI
* prioritaria sulle zone non ancora viste

### Task

* definire rappresentazione ROI nel file `ANNOTATION`
* implementare interfaccia per disegnare ROI
* calcolare quali patch intersecano una ROI
* decidere se includere patch:

  * completamente contenute
  * parzialmente intersecanti
  * sopra una soglia minima di intersezione

### Criteri di accettazione

* il programma sa identificare in modo deterministico le patch candidate
* la percentuale richiesta viene applicata sulle patch eleggibili
* la selezione è riproducibile se serve

---

## 5. Vincolo patch quadrata

### Obiettivo

Rendere esplicito il vincolo che ogni patch deve avere forma quadrata.



* gestione del bordo immagine quando le dimensioni non sono multiple della patch

### Decisioni da prendere

* come trattare le patch 'incomplete' ai bordi 

  * --> **scartarle**
  * pad con zeri / sfondo
  * includerle con metadato `partial_patch=true`

### Task

* modificare input patch size
* definire politica di gestione bordi

 

---

## 6. Visualizzazione patch una per volta

### Obiettivo

Mostrare al medico una patch per volta in modo semplice, rapido e sicuro.

### Requisiti funzionali

* visualizzazione patch corrente
* pulsanti o shortcut per:

  * etichettare
  * saltare
  * tornare indietro
  * aggiungere nota
* indicatore di progresso
* possibilità di vedere ID patch e metadati essenziali
* eventuale zoom della patch

### Stati patch

* pending
* shown
* labeled
* skipped
* flagged_for_review

### Task

* progettare UI minimale per revisione rapida
* introdurre scorciatoie da tastiera
* distinguere chiaramente “skip” da “non ancora vista”
* salvare timestamp e utente annotatore

### Criteri di accettazione

* ogni azione dell’utente aggiorna immediatamente lo stato della patch
* il medico può completare una sequenza senza usare menu complessi

---

## 7. Sistema di labeling e annotazioni

### Obiettivo

Consentire etichettatura consistente e annotazioni testuali strutturate.

### Requisiti

* insieme di label configurabile
* possibilità di aggiungere nota libera
* eventuale supporto a:

  * confidenza
  * severità
  * multi-label
  * flag “da rivedere”

### Task

* definire tassonomia label
* validare le label ammesse
* separare:

  * label clinica principale
  * note testuali
  * metadati operativi
* valutare storico modifiche label (in futuro)

### Criteri di accettazione

* ogni patch può essere etichettata in modo coerente
* una modifica successiva è tracciabile se richiesto (in futuro)

---

## 8. Overlay dell’immagine principale con colori per etichetta

### Obiettivo

Mostrare l’immagine principale con patch colorate in base all’etichetta assegnata.

### Requisiti

* visualizzazione griglia patch su immagine originale
* colore diverso per ogni label
* colori distinti anche per:

  * pending
  * skipped
  * flagged
* click su patch per aprire dettaglio
* legenda colori

### Vincoli

Questo è possibile solo se:

* esiste immagine originale oppure
* esistono coordinate patch riconducibili a un canvas comune

### Task

* definire palette/stato-colore
* costruire overlay efficiente
* aggiornare overlay in tempo reale dopo ogni annotazione
* gestire visibilità layer on/off

### Criteri di accettazione

* il medico può capire a colpo d’occhio quali aree sono state già etichettate
* l’overlay è coerente con i dati presenti in `ANNOTATION`

---

## 9. Gestione del caso “patch folder senza coordinate”

### Obiettivo

Supportare la valutazione anche quando non si può ricostruire la posizione originaria delle patch.

### Requisiti

* usare nome file patch come identificativo o derivarne uno stabile
* consentire annotazione completa
* rinunciare solo alle funzioni che dipendono dalla geometria

### Limitazioni da esplicitare

* niente overlay sull’immagine originale
* niente ROI geometriche sull’immagine originale, salvo coordinate esterne
* progress tracking comunque disponibile

### Task

* definire identificazione robusta delle patch da file
* evitare dipendenze obbligatorie dalle coordinate
* gestire ordinamento patch deterministico

### Criteri di accettazione

* il programma resta pienamente utilizzabile anche senza coordinate
* le feature non disponibili vengono disabilitate in modo chiaro

---

## 10. Regole di identificazione e tracciabilità patch

### Obiettivo

Garantire che ogni patch sia riconoscibile in modo univoco.

### Requisiti

* `patch_id` univoco
* se generata dal programma: ID derivato da coordinate o indice
* se caricata da cartella: ID derivato da filename o hash
* tracciabilità tra patch mostrata e record annotato

### Task

* definire convenzione di naming
* evitare duplicati
* validare collisioni di nome in cartella

### Criteri di accettazione

* non esistono due patch con lo stesso ID nello stesso caso
* ogni annotazione è sempre riconducibile a una patch precisa

---

## 11. Persistenza, salvataggio e robustezza

### Obiettivo

Evitare perdita dati e corruzione del file di annotazione.

### Requisiti

* salvataggio atomico
* autosave dopo ogni azione
* backup/versioni del file `ANNOTATION`
* recovery in caso di chiusura anomala

### Task

* implementare scrittura sicura su file temporaneo + rename
* creare checkpoint periodici
* validare JSON prima del salvataggio
* loggare errori di I/O

### Criteri di accettazione

* un crash non compromette l’intera sessione
* l’ultimo stato consistente è recuperabile

---

## 12. Configurazione del progetto

### Obiettivo

Rendere configurabili gli aspetti variabili senza modificare codice.

### Parametri configurabili

* dimensione patch
* overlap
* politica bordi
* etichette disponibili
* colori label
* scorciatoie da tastiera
* strategia di campionamento
* percentuale di default

### Task

* introdurre file di configurazione
* validare configurazione in avvio
* prevedere valori di default sensati

### Criteri di accettazione

* il comportamento base del programma può essere adattato via config

---

## 13. Audit trail e revisione annotazioni

(in seguito)

### Obiettivo

Consentire modifica e revisione mantenendo traccia di chi ha fatto cosa.

### Requisiti opzionali ma consigliati

* storico modifiche
* utente annotatore
* timestamp creazione/modifica
* motivo della modifica

### Task

* valutare se salvare solo stato finale o storico completo
* introdurre campo `history` per patch o log sessione separato

### Criteri di accettazione

* una patch modificata in revisione può essere tracciata

---

## 14. Export dati

### Obiettivo

Permettere uso successivo delle annotazioni per training, report o QA.

### Export utili

* elenco patch etichettate per label
* pandas/excel
* eventuale manifest per dataset ML
* ...

### Task

* definire schema export tabellare
* esportare solo patch annotate o tutte
* includere metadati minimi per training

### Criteri di accettazione

* i dati annotati possono essere riutilizzati facilmente fuori dal programma

---

## 15. Gestione edge case

### Obiettivo

Coprire situazioni ambigue o problematiche.

### Casi da gestire

* cartella patch vuota
* file immagine non leggibile
* patch duplicate
* `ANNOTATION` corrotto o incompatibile
* ROI senza patch eleggibili
* percentuale = 0 o 100
* patch già tutte annotate
* cambio dimensione patch su immagine già annotata

### Task

* definire messaggi di errore chiari
* introdurre validazioni all’apertura
* bloccare configurazioni incompatibili con sessioni esistenti

### Criteri di accettazione

* il programma fallisce in modo controllato, non ambiguo

---
---

# User stories  

## Epic: Gestione input

* Come utente, voglio caricare un’immagine istologica intera, così che il sistema possa dividerla automaticamente in patch.
* Come utente, voglio caricare una cartella di patch già esistenti, così da evitare la fase di patching.
* Come sistema, voglio uniformare i due tipi di input in una rappresentazione interna comune, così da riutilizzare lo stesso flusso di annotazione.

## Epic: Annotazione

* Come medico, voglio visualizzare una patch per volta
* Come medico, voglio assegnare una label e aggiungere note.
* Come medico, voglio saltare una patch o marcarla per revisione,  
* 
## Epic: Continuità del lavoro

* Come utente, voglio interrompere e riprendere una sessione, così da non perdere il lavoro svolto.
* Come sistema, voglio salvare automaticamente ogni annotazione, così da ridurre il rischio di perdita dati.

## Epic: Visualizzazione globale

* Come medico, voglio vedere l’immagine originale con patch colorate per etichetta, così da capire la distribuzione spaziale delle annotazioni.
* Come medico, voglio vedere il progresso complessivo dell’analisi, così da sapere quanto lavoro resta da fare.

---

# Riflettere su questo

Distinzione importante tra:

* **patch candidate**
* **patch selezionate per review**
* **patch effettivamente annotate**

Questa distinzione è utile perché:

* una patch può essere dentro una ROI ma non scelta nel campionamento
* una patch può essere scelta ma ancora non mostrata
* una patch può essere mostrata ma saltata
* una patch può essere rivista più volte

Quindi conviene avere campi separati:

* `eligible`
* `selected_for_review`
* `shown_to_user`
* `status`

---