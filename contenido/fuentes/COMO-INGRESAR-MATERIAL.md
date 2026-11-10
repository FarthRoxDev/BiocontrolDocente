# Cómo ingresar el material de los docentes

El material original vive fuera del repo (OneDrive del TEC). Para procesarlo hay
tres caminos, de más a menos cómodo:

## 1. Repo local (recomendado)
Clonar el repo en la máquina donde está OneDrive, copiar los archivos a
`contenido/fuentes/` y correr el ingestor. El repo ignora binarios grandes, así
que conviene commitear solo los `01-fuente.md` resultantes, no los .pptx.

## 2. Carpeta compartida por Remote Control
En la app de escritorio de Claude: Ajustes → Claude Code → Remote Control, y
compartir la carpeta `TEC/Biocontrol`. A partir de ahí una sesión en la nube
puede leerla directamente.

## 3. Subir los archivos al chat
Adjuntar los .pptx/.docx/.pdf en la conversación; se procesan y se devuelven
los `01-fuente.md`.

Después, para cada capítulo:

```bash
python3 build/scripts/ingerir_fuentes.py contenido/fuentes/<archivos> --capitulo cap01 --docente "Nombre del docente"
```
