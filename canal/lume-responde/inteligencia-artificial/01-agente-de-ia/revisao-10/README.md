# Lume Responde 01 · v10 de revisão

O [corte v10](../Lume-Responde-01-v10.mp4) usa a imagem e os pacotes de áudio da [v9](../Lume-Responde-01-v9.mp4). O [mapa de cenas](olhar-cenas.json) faz o Lume seguir elementos da demonstração e voltar a olhar para a câmera. A [base do avatar](../../../../assets/avatar-512/) guarda a expressão de câmera em todos os estados de luz.

As [marcas de palavra](legendas.json) seguem a locução de 03h16. A letra em destaque cresce e influencia as três posições vizinhas em cada direção. O trecho da pergunta mantém a cartela da v9.

## Reexportar

Use Python, Pillow, NumPy, FFmpeg com libx264 e a fonte [KnockIt! Display Research v0.15](https://chatgpt.com/library?file_id=libfile_9d87cc7de5bc81918485da9ecd624e43&account_id=personal). A partir desta pasta:

```sh
python3 compose.py --font /caminho/KnockIT_Display_Research_v0.15.ttf ../Lume-Responde-01-v10.mp4
```
