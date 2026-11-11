# Montar el proyecto en tu máquina (Windows)

Pensado para trabajar con **Claude Code en la terminal**, dentro del repo.
Todo esto se hace una sola vez.

> **Antes que nada: ¿cmd o PowerShell?**
> Los comandos de abajo están escritos para **cmd** (la ventana negra clásica),
> porque es la que se abre por defecto. Funcionan igual en PowerShell salvo una
> línea, que está marcada.
>
> **Nunca junte dos comandos con `;` en cmd**: cmd no lo entiende como separador
> y el segundo comando se pierde sin avisar. Un comando por línea, siempre.

---

## 0. Requisitos previos

| | Cómo comprobar | Si falta |
|---|---|---|
| Git | `git --version` | https://git-scm.com/download/win |
| Python 3.10+ | `py --version` | https://www.python.org/downloads/ (marcar **Add to PATH**) |
| Node.js | `node --version` | https://nodejs.org (versión LTS) |
| Claude Code | `claude --version` | `npm install -g @anthropic-ai/claude-code` |
| Chrome o Edge | ya viene en Windows | — |

Node **no** hace falta para construir los entregables, pero **sí** para instalar
Claude Code, que se distribuye por npm. Si `claude` responde «no se reconoce
como un comando», es que falta ese paso (o que hay que cerrar y volver a abrir
la terminal para que tome el PATH nuevo).

---

## 1. Clonar el repo

Elegí una carpeta corta y sin espacios. El material de los docentes se queda
donde está: **no hay que moverlo**.

Un comando por línea. Si `C:\Proyectos` ya existe, el `mkdir` avisa y no pasa
nada: siga con el resto.

```bat
mkdir C:\Proyectos
```

```bat
cd /d C:\Proyectos
```

```bat
git clone https://github.com/FarthRoxDev/BiocontrolDocente.git
```

```bat
cd BiocontrolDocente
```

```bat
git checkout claude/jolly-bardeen-mlivgy
```

El `/d` del `cd` es necesario para cambiar de unidad (de `C:` a `D:`, por
ejemplo). Cuesta nada ponerlo siempre.

---

## Atajo: `montar.bat`

Una vez clonado el repo y parado dentro de su carpeta, esto hace los pasos 2 y 3
de una sola vez (rama, entorno, dependencias, Chromium y comprobación):

```bat
montar.bat
```

Si preferís hacerlo paso a paso, seguí abajo.

## 2. Entorno de Python

```bat
py -m venv .venv
```

Activarlo. **Esta es la línea que cambia según la terminal:**

```bat
.venv\Scripts\activate.bat
```

> En PowerShell es `.\.venv\Scripts\Activate.ps1`. Si PowerShell se queja con
> «la ejecución de scripts está deshabilitada», corra
> `Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned`
> una vez en esa misma ventana y repita el activate.

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
| `The system cannot find the path specified` | se juntaron dos comandos con `;` en cmd: van en líneas separadas |
| `'claude' is not recognized` | falta `npm install -g @anthropic-ai/claude-code`, o cerrar y reabrir la terminal |
| El PDF sale sin una imagen | es un EMF/WMF o un gráfico nativo de PowerPoint: el ingestor lo avisa y hay que reexportarlo a PNG |
| `verificar_sync` marca DESFASE | el libro cambió de largo: reconstruirlo y ajustar los `pagina:` de las diapositivas |
