@echo off
REM ===================================================================
REM  Montaje del proyecto en Windows. Se corre UNA vez, desde la
REM  carpeta del repositorio:   montar.bat
REM ===================================================================
setlocal

echo.
echo [1/5] Comprobando requisitos...
where py >nul 2>&1 || (echo FALTA Python. Instalalo desde https://www.python.org/downloads/ y marca "Add to PATH". & exit /b 1)
where git >nul 2>&1 || (echo FALTA Git. Instalalo desde https://git-scm.com/download/win & exit /b 1)

echo.
echo [2/5] Trayendo la rama de trabajo...
git checkout claude/jolly-bardeen-mlivgy || exit /b 1
git pull origin claude/jolly-bardeen-mlivgy || exit /b 1

echo.
echo [3/5] Creando el entorno de Python...
if not exist .venv\Scripts\python.exe py -m venv .venv || exit /b 1

echo.
echo [4/5] Instalando dependencias (tarda unos minutos)...
.venv\Scripts\python.exe -m pip install --quiet --upgrade pip
.venv\Scripts\python.exe -m pip install --quiet -r requisitos.txt || exit /b 1
.venv\Scripts\python.exe -m playwright install chromium || exit /b 1

echo.
echo [5/5] Comprobando el entorno...
.venv\Scripts\python.exe build\scripts\comprobar_entorno.py

echo.
echo ===================================================================
echo  Listo. Para trabajar, activa el entorno en cada ventana nueva:
echo.
echo      .venv\Scripts\activate.bat
echo.
echo  Y despues construi un capitulo con:
echo.
echo      python build\scripts\construir_libro.py --capitulo cap01
echo ===================================================================
endlocal
