# Ksenia Lares - Automazioni e Device Actions

Questa integrazione supporta **Device Triggers, Actions e Conditions** che permettono di creare automazioni facilmente dall'interfaccia grafica di Home Assistant.

## 📋 Device Triggers

I device triggers permettono di avviare automazioni quando si verificano eventi specifici:

### Allarme (Alarm Control Panel)
- **Alarm Triggered** - L'allarme è stato attivato
- **Alarm Armed Away** - L'allarme è stato inserito in modalità "fuori casa"
- **Alarm Armed Home** - L'allarme è stato inserito in modalità "in casa"
- **Alarm Armed Night** - L'allarme è stato inserito in modalità "notte"
- **Alarm Disarmed** - L'allarme è stato disinserito
- **Alarm Arming** - L'allarme si sta inserendo (countdown)
- **Alarm Pending** - L'allarme è in pre-allarme

### Zone (Sensori)
- **Zone Opened** - Una zona (porta/finestra) è stata aperta
- **Zone Closed** - Una zona è stata chiusa
- **Zone Alarm** - Una zona è in stato di allarme

## 🎯 Device Actions

Le device actions permettono di controllare i dispositivi Ksenia Lares:

### Allarme
- **Arm Away** - Inserisci allarme in modalità "fuori casa"
- **Arm Home** - Inserisci allarme in modalità "in casa"
- **Arm Night** - Inserisci allarme in modalità "notte"
- **Disarm** - Disinserisci allarme
- **Trigger** - Attiva manualmente l'allarme

### Zone (Bypass)
- **Zone Bypass** - Escludi una zona
- **Zone Unbypass** - Riattiva una zona esclusa

### Uscite (Outputs)
- **Output Turn On** - Attiva un'uscita
- **Output Turn Off** - Disattiva un'uscita

## ✅ Device Conditions

Le device conditions permettono di verificare lo stato dei dispositivi:

### Allarme
- **Is Triggered** - Verifica se l'allarme è scattato
- **Is Armed Away** - Verifica se è inserito in modalità "fuori casa"
- **Is Armed Home** - Verifica se è inserito in modalità "in casa"
- **Is Armed Night** - Verifica se è inserito in modalità "notte"
- **Is Disarmed** - Verifica se è disinserito
- **Is Arming** - Verifica se si sta inserendo
- **Is Pending** - Verifica se è in pre-allarme

### Zone
- **Is Opened** - Verifica se una zona è aperta
- **Is Closed** - Verifica se una zona è chiusa
- **Is Bypassed** - Verifica se una zona è esclusa
- **Is Not Bypassed** - Verifica se una zona non è esclusa

### Uscite
- **Is On** - Verifica se un'uscita è attiva
- **Is Off** - Verifica se un'uscita è disattivata

## 📘 Blueprints Inclusi

L'integrazione include blueprint pronti all'uso per scenari comuni:

### 1. Alarm Triggered Notification
Invia una notifica quando l'allarme viene attivato.

**Caratteristiche:**
- Notifica personalizzabile (titolo e messaggio)
- Supporto per azioni nella notifica
- Alta priorità per notifiche immediate

### 2. Zone Opened Notification
Invia una notifica quando una zona specifica viene aperta.

**Caratteristiche:**
- Monitoraggio zona singola
- Opzione per notificare solo quando l'allarme è inserito
- Notifiche personalizzabili

### 3. Auto Arm Away
Inserisce automaticamente l'allarme quando tutti lasciano casa.

**Caratteristiche:**
- Ritardo configurabile prima dell'inserimento
- Verifica opzionale che porte/finestre siano chiuse
- Basato su entità di presenza (person, group, zone)

### 4. Auto Disarm
Disinserisce automaticamente l'allarme quando qualcuno arriva a casa.

**Caratteristiche:**
- Restrizioni temporali opzionali
- Verifica dello stato attuale dell'allarme
- Supporto per device_tracker e person

## 🚀 Come Usare

### Creare un'automazione dall'UI

1. Vai in **Impostazioni** → **Automazioni e Scene** → **Crea Automazione**
2. Seleziona il tipo di trigger desiderato
3. Cerca "Ksenia Lares" nei dispositivi disponibili
4. Seleziona il trigger/action/condition specifico
5. Configura le opzioni

### Importare un Blueprint

1. Vai in **Impostazioni** → **Automazioni e Scene** → **Blueprint**
2. Clicca su **Importa Blueprint**
3. Inserisci l'URL del blueprint da questo repository:
   ```
   https://github.com/chiuky/ha-ksenia-lares/blob/main/custom_components/ksenia_lares/blueprints/automation/[nome_blueprint].yaml
   ```
4. Configura i parametri richiesti

### Esempio YAML manuale

```yaml
automation:
  - alias: "Notifica allarme attivato"
    trigger:
      - platform: device
        device_id: abc123...
        domain: ksenia_lares
        type: alarm_triggered
    action:
      - service: notify.mobile_app_iphone
        data:
          title: "🚨 Allarme Attivato!"
          message: "L'allarme Ksenia Lares è stato attivato!"

  - alias: "Inserisci allarme quando esco"
    trigger:
      - platform: state
        entity_id: person.mario
        to: "not_home"
        for:
          minutes: 5
    condition:
      - condition: device
        device_id: abc123...
        domain: ksenia_lares
        type: is_disarmed
    action:
      - service: alarm_control_panel.alarm_arm_away
        target:
          device_id: abc123...
```

## 🔧 Personalizzazione

Puoi creare automazioni personalizzate combinando:
- **Triggers** (quando qualcosa accade)
- **Conditions** (se certe condizioni sono vere)
- **Actions** (cosa fare)

Esempio avanzato:
```yaml
automation:
  - alias: "Allarme intelligente notturno"
    trigger:
      - platform: time
        at: "23:00:00"
    condition:
      - condition: state
        entity_id: group.famiglia
        state: "home"
      - condition: device
        device_id: abc123...
        domain: ksenia_lares
        type: is_disarmed
    action:
      - service: alarm_control_panel.alarm_arm_night
        target:
          device_id: abc123...
      - service: notify.family
        data:
          message: "Allarme inserito in modalità notte"
```

## 📚 Documentazione Aggiuntiva

Per maggiori informazioni su come creare automazioni in Home Assistant:
- [Documentazione Automazioni](https://www.home-assistant.io/docs/automation/)
- [Blueprint](https://www.home-assistant.io/docs/automation/using_blueprints/)
- [Device Triggers](https://www.home-assistant.io/docs/device_automation/)

## 🐛 Troubleshooting

**Le device actions non appaiono nell'UI**
- Verifica che l'integrazione sia aggiornata
- Riavvia Home Assistant dopo l'aggiornamento
- Controlla i log per eventuali errori

**Le notifiche non arrivano**
- Verifica che il servizio di notifica mobile sia configurato
- Controlla che il device_id sia corretto
- Testa la notifica manualmente dal Developer Tools

**L'automazione non si attiva**
- Verifica che i trigger siano configurati correttamente
- Controlla lo stato delle entità coinvolte
- Abilita il debug logging per l'integrazione
