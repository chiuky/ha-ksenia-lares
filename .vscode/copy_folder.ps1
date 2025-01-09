param (
    [Parameter(Mandatory = $true, HelpMessage = "Percorso della cartella sorgente")]
    [string]$sourcePath,

    [Parameter(Mandatory = $true, HelpMessage = "Percorso della cartella di destinazione")]
    [string]$destinationPath
)

# Log di inizio script
Write-Host "Inizio script: copia della cartella da '$sourcePath' a '$destinationPath'" -ForegroundColor Green

try {
    # Controllo se la cartella di destinazione esiste
    if (-Not (Test-Path -Path $destinationPath)) {
        Write-Host "La cartella di destinazione non esiste. Creazione della cartella..." -ForegroundColor Yellow
        # Creazione della cartella se non esiste
        New-Item -ItemType Directory -Path $destinationPath | Out-Null
        Write-Host "Cartella di destinazione creata con successo." -ForegroundColor Green
    } else {
        Write-Host "La cartella di destinazione esiste gia'!  Procedo con la copia dei file..." -ForegroundColor Cyan
    }

    # Copia dei file e delle sottocartelle
    Copy-Item -Path "$sourcePath\*" -Destination $destinationPath -Recurse -Force
    Write-Host "Copia completata con successo!" -ForegroundColor Green
} catch {
    # Gestione degli errori
    Write-Host "Errore durante l'esecuzione dello script: $_" -ForegroundColor Red
}

# Log di completamento script
Write-Host "Script completato." -ForegroundColor Green
