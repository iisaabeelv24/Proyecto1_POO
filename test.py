from pathlib import Path

p = Path()

for x in p.iterdir():
    print(x)
    if x.is_dir():
        print("Directorio:", x)
        print("Contenido:", [y for y in x.iterdir()])
