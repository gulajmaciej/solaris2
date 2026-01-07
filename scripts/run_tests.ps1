param(
    [string]$Marker = "unit"
)

if ($Marker -eq "all") {
    python -m pytest
    exit $LASTEXITCODE
}

python -m pytest -m $Marker
exit $LASTEXITCODE
