# Sistema de Ojos y Boca para Dino

## Arquitectura (mismo patron que Lumi)

```
ojos-boca-system/
├── README.md
├── eyes.js          # overlay de ojos PNG sobre la malla
├── mouth.js         # overlay de boca SVG sobre la malla
├── test.html        # pagina de prueba con dino GLB + sliders
└── assets/
    ├── ojo_abierto.png
    ├── ojo_medio.png
    ├── ojo_cerrado.png
    └── bocas/       # 8 visemas SVG
        ├── X.svg    # cerrada
        ├── A.svg    # abierta_ah
        ├── B.svg    # apenas_abierta
        ├── C.svg    # eh
        ├── D.svg    # ah_grande
        ├── E.svg    # oh_redonda
        ├── F.svg    # oo_apretada
        └── G.svg    # dientes_labio
```

## Hueso target
- `Head` (o el que tenga el GLB del dino)

## Parametros ajustables (por slider)
- X, Y, Z por ojo
- Escala por ojo
- X, Y, Z de la boca
- Escala de la boca
- Curvatura del plano (para seguir la cara)

## Flujo
1. Cargar GLB del dino
2. Encontrar hueso `Head`
3. Crear PlanoBufferGeometry con textura PNG (ojos) / SVG (boca)
4. depthTest=false, renderOrder=999
5. Posicionar con coordenadas calibrables
6. Re-alinear cada frame (opcional, como el fix de Lumi)

## Estados de ojo
- open: opacity=1, visible=true
- mid: opacity=0.7
- closed: opacity=0.1

## Estados de boca (8 visemas)
- Mismo sistema que Lumi: cambiar material.map al SVG correspondiente
