# Montar el proyecto en tu máquina (Windows)

Pensado para trabajar con **Claude Code en la terminal**, dentro del repo.
Todo esto se hace una sola vez.

---

## 0. Requisitos previos

| | Cómo comprobar | Si falta |
|---|---|---|
| Git | `git --version` | https://git-scm.com/download/win |
| Python 3.10+ | `py --version` | https://www.python.org/downloads/ (marcar **Add to PATH**) |
| Claude Code | `claude --version` | `npm i -g @anthropic-ai/claude-code` |
| Chrome o Edge | ya viene en Windows | — |

No hace falta Node para construir los entregables (sí para instalar Claude Code).

---

## 1. Clonar el repo

Elegí una carpeta corta y sin espacios. El material de los docentes se queda
donde está: **no hay que moverlo**.

```powershell
mkdir C:\Proyectos
cd C:\Proyectos
git clone https://github.com/FarthRoxDev/BiocontrolDocente.git
cd BiocontrolDocente
git checkout claude/jolly-bardeen-mlivgy
```

---

## 2. Entorno de Python

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
```

> Si PowerShell se queja con «la ejecución de scripts está deshabilitada»,
> corré esto una vez en esa misma ventana y repetí el activate:
> `Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned`
>
> En `cmd` en vez de PowerShell, el activate es `.venv\Scripts\activate.bat`.

Con el entorno activo (verás `(.venv)` al principio de la línea):

```powershell
pip install -r requisitos.txt
```

```powershell
python -m playwright install chromium
```

El último paso se puede saltar si ya tenés Chrome o Edge: el proyecto los
usa como respaldo. Descargarlo igual da resultados más consistentes.

---

## 3. Comprobar que todo está

```powershell
python build\scripts\comprobar_entorno.py
```

Tiene que terminar en «Todo listo». Si algo falta, la salida dice el comando
exacto para arreglarlo.

---

## 4. Abrir Claude Code en el proyecto

```powershell
claude
```

Se abre **dentro de la carpeta del repo**, así que lee solo el `CLAUDE.md`
y las cinco skills de `.claude/skills/`, que viajan con el clon.

---

## Trabajo del día a día

**Antes de empezar**, traer lo que se haya hecho en la nube:

```powershell
git pull origin claude/jolly-bardeen-mlivgy
```

**Ingerir material nuevo** de un docente. La ruta va entre comillas porque
tiene espacios, y se puede apuntar a la carpeta entera:

```powershell
python build\scripts\ingerir_fuentes.py "C:\Users\rojas\3D Objects\BiocontrolCapaci" --capitulo cap04 --docente "Nombre del docente"
```

**Construir los tres entregables** de un capítulo:

```powershell
python build\scripts\construir_libro.py --capitulo cap01
```

```powershell
python build\scripts\construir_libro.py --capitulo cap01 --edicion docente
```

```powershell
python build\scripts\construir_presentacion.py --capitulo cap01
```

```powershell
python build\scripts\verificar_sync.py --capitulo cap01
```

Los PDF y el PPTX quedan en `salidas\`. Esa carpeta está en `.gitignore`:
los entregables se reconstruyen, no se versionan.

**Al terminar**, subir el trabajo:

```powershell
git add -A
```

```powershell
git commit -m "describir qué se hizo"
```

```powershell
git push origin claude/jolly-bardeen-mlivgy
```

---

## Si algo falla

| Síntoma | Causa casi siempre |
|---|---|
| `no se pudo abrir Chromium` | falta `python -m playwright install chromium` |
| `ModuleNotFoundError` | el entorno virtual no está activo (no aparece `(.venv)`) |
| `nada coincide con: *.pptx` | la ruta está mal escrita, o falta ponerla entre comillas |
| El PDF sale sin una imagen | es un EMF/WMF o un gráfico nativo de PowerPoint: el ingestor lo avisa y hay que reexportarlo a PNG |
| `verificar_sync` marca DESFASE | el libro cambió de largo: reconstruirlo y ajustar los `pagina:` de las diapositivas |
