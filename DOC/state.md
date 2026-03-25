# State

## - Stato Attuale


L'applicazione permette il caricamento di immagini istologiche o di dataset di patch istologiche. 
Nel caso in cui venga caricata un'immagine istologica intera, il programma effettuerà il "ritaglio" in patch (grandezza impostata dall'utente).  
Una volta caricati i file in input, verranno presentate all'utente le patch (ordine sequenziale o random a discrezione dell'utente), che potrà assegnare a ciascuna di esse un'etichetta (allo stato attuale "Tumor" o "Normal").  
Terminata l'etichettatura le patch verranno salvate nel path di output in locale selezionato dall'utente assieme a un file.csv (contenente nome patch, coordinate, etichetta) nel path di output in locale selezionato dall'utente.  


La manipolazione delle slide istopatologiche è effettuata tramite l'utilizzo della libreria PyVips, permettendo un approccio completamente lazy loading con immagini di rilevanti dimensioni, quali slide istologiche.  


L'architettura di modulazione utilizzata è la MVC (Model - View - Controller).

## - Stato dell'Implementazione Visiva
Per l'interfaccia è stata scelta la libreria PySide6, che permette di utilizzare il framework Qt6 (C++).

---
### 1. Pagina di Start
<img width="301" height="252" alt="page_start" src="https://github.com/user-attachments/assets/ab5b54a6-5c41-46aa-b31c-461285aa9790" />

Nella pagina iniziale l'utente ha la possibilità di selezionare la modalità di input (Slide/Dataset) e seleziona il percorso di output in cui saranno salvati i dati.  

---
### 2. Pagina Setting Slide
<img width="301" height="252" alt="page_setting_slide" src="https://github.com/user-attachments/assets/f99eef96-642c-4afc-8c67-d0e085f53123" />

Nel caso in cui l'utente selezioni l'input da Slide, verrà portato nella pagina di setaggio Slide.  
  
In questa schermata l'utente seleziona il path di input della slide, imposta la dimensiona desiderata delle patch, seleziona la modalità e l'ordine di visualizzazione delle patch.  
  
Attraverso il bottone "Verifica Griglia" l'utente accederà a un'altra schermata in cui visualizzerà un'anteprima della slide con anteposta la griglia con le dimensioni da lui impostate. Possiamo vederne la rappresentazione nella seguente figura:

<img width="301" height="252" alt="page_grid" src="https://github.com/user-attachments/assets/f524d45b-27c1-4aee-b0af-9188549948e2" />  

---
### 2.1 Page Total Slide
<img width="301" height="252" alt="page_total_slide" src="https://github.com/user-attachments/assets/a2211cab-fdce-4233-ba18-98d0b6d34ef0" />

Nel caso in cui l'utente abbia selezionato la modalità "Slide intera" le verrà presentata l'intera slide istologica, con anteposta la griglia della grandezza da lui impostata.  
  
Effettuando un "doppio-click" su una patch, questa verrà mostrata all'utente nel riquadro a destra e potrà assegnarle un'etichetta tramite i bottoni.  

---
### 2.2 Page Single Patch
<img width="301" height="252" alt="page_patch_dataset" src="https://github.com/user-attachments/assets/9c8978c3-b73a-4054-b93d-67db33592fac" />

Nel caso in cui l'utente abbia selezionato la modalità "Patch singole" l'applicazione calcolerà tutte le coordinate delle patch (con grandezza impostata dall'utente) e, se conterranno tessuto, verranno presentate all'utente che dovrà assegnarle un'etichetta tramite i bottoni.  

---
### 3. Page Setting Dataset
<img width="301" height="252" alt="page_setting_dataset" src="https://github.com/user-attachments/assets/a1709320-8f7c-495f-9940-6ceb82a02cdc" />

Nel caso in l'utente selezioni l'input da Dataset, verrà portato nella pagina di setaggio Dataset.  
  
In questa schermata l'utente inserirà il path del dataset che contiene le patch istologiche e dovrà selezionare l'ordine di visualizzazione.  
  
**NOTA BENE:** la schermata utilizzata per la visualizzazione e l'etichettatura delle patch caricate attraverso un Dataset è la stessa utilizzata per la suddivisione in patch di una Slide (punto 2.29).  




