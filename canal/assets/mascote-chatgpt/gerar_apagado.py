#!/usr/bin/env python3
"""Gera a versão "apagada" do mascote Lume (ChatGPT) e um GIF de pulso.

Entradas (relativas a este arquivo):
  ../avatar-512/sprites/lume-acendimento-01.png   abdômen apagado (malva/lilás)
  ../avatar-512/sprites/lume-acendimento-18.png   abdômen aceso (âmbar/dourado)
  ./Lume-mascote-chatgpt.png                      1536x2288 RGBA, 11 linhas x 8 colunas
                                                  de células 192x208

Saídas:
  ./Lume-mascote-chatgpt-apagado.png              1536x2288 RGBA
  ./Lume-pulso-preview.gif                        linha 0 (idle) pulsando apagado <-> aceso

Como funciona:
  1. Compara os pixels do abdômen aceso (frame 18) com os mesmos pixels apagados
     (frame 01) e monta uma rampa luminância -> RGB malva/lilás. A rampa é indexada
     por percentil de luminância, então o sombreado/realce é preservado.
  2. No mascote, seleciona só pixels âmbar/dourado/laranja (matiz ~10-58 graus,
     S > 0.25, V > 0.25) com máscara suave (bordas sem serrilhado) e filtro espacial
     por componente conexo por célula (descarta línguas, brilhos nos olhos etc.).
  3. Remapeia esses pixels para a rampa apagada, mantendo o alfa exato.

Requer: Python 3, Pillow, NumPy (SciPy é opcional e só acelera a rotulagem).
"""

from pathlib import Path

import numpy as np
from PIL import Image

# --------------------------------------------------------------------------- #
# Caminhos
# --------------------------------------------------------------------------- #
AQUI = Path(__file__).resolve().parent
ASSETS = AQUI.parent
SPRITES = ASSETS / "avatar-512" / "sprites"

FRAME_APAGADO = SPRITES / "lume-acendimento-01.png"
FRAME_ACESO = SPRITES / "lume-acendimento-18.png"
SHEET = AQUI / "Lume-mascote-chatgpt.png"
OUT_PNG = AQUI / "Lume-mascote-chatgpt-apagado.png"
OUT_GIF = AQUI / "Lume-pulso-preview.gif"

# --------------------------------------------------------------------------- #
# Parâmetros
# --------------------------------------------------------------------------- #
ROWS, COLS = 11, 8

# Seleção do abdômen aceso (HSV). Cada limite é suavizado (feather) para as
# bordas ficarem limpas: o peso vale 0.5 exatamente no limite.
HUE_MIN, HUE_MAX = 10.0, 58.0   # graus
HUE_FEATHER = 4.0               # graus
SAT_MIN, SAT_FEATHER = 0.25, 0.06
VAL_MIN, VAL_FEATHER = 0.25, 0.06
ALPHA_MIN = 0.03                # ignora pixels praticamente transparentes

# Sanidade espacial por célula (componentes conexos da máscara).
CAND_THRESHOLD = 0.12           # peso mínimo para um pixel ser candidato
MIN_COMP_AREA = 6               # px; componentes menores que isso (exceto o maior) caem
MIN_COMP_REL = 0.08             # área mínima relativa ao maior componente
LOWER_FRAC = 0.30               # componente secundário precisa estar abaixo de 30% da altura
                                # do personagem na célula (abdômen fica embaixo; boca/olhos em cima)

# Rampa
RAMP_SIZE = 256
QUANT_POINTS = 512
MIN_RAMP_PIXELS = 50

# Mauve de reserva (se os frames 01/18 não forem pareáveis pixel a pixel)
MAUVE_HUE = (250.0, 340.0)
MAUVE_SAT_MIN = 0.12

# GIF
GIF_BG = (1, 1, 44)             # #01012C
GIF_FRAMES = 32                 # 4 ciclos de idle (8 quadros) = 2 pulsos completos
GIF_PULSE_PERIOD = 16           # quadros por pulso (apagado -> aceso -> apagado)
GIF_DURATION_MS = 100
GIF_SCALE = 2                   # ampliação (vizinho mais próximo) para inspeção


# --------------------------------------------------------------------------- #
# Utilitários de cor
# --------------------------------------------------------------------------- #
def rgb_to_hsv(rgb):
    """rgb float (...,3) em 0..1 -> (h em graus 0..360, s, v)."""
    r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    mx = rgb.max(axis=-1)
    mn = rgb.min(axis=-1)
    d = mx - mn
    safe = np.where(d > 1e-8, d, 1.0)
    h = np.zeros_like(mx)
    m_r = (mx == r) & (d > 1e-8)
    m_g = (mx == g) & (d > 1e-8) & ~m_r
    m_b = (d > 1e-8) & ~m_r & ~m_g
    h = np.where(m_r, ((g - b) / safe) % 6.0, h)
    h = np.where(m_g, (b - r) / safe + 2.0, h)
    h = np.where(m_b, (r - g) / safe + 4.0, h)
    h = h * 60.0
    s = np.where(mx > 1e-8, d / np.where(mx > 1e-8, mx, 1.0), 0.0)
    return h, s, mx


def luminance(rgb):
    return (0.2126 * rgb[..., 0] + 0.7152 * rgb[..., 1] + 0.0722 * rgb[..., 2])


def smoothstep(x, e0, e1):
    t = np.clip((x - e0) / (e1 - e0), 0.0, 1.0)
    return t * t * (3.0 - 2.0 * t)


def amber_weight(rgb, alpha):
    """Peso 0..1 de 'pixel âmbar/dourado/laranja do abdômen aceso'."""
    h, s, v = rgb_to_hsv(rgb)
    w_h = smoothstep(h, HUE_MIN - HUE_FEATHER, HUE_MIN + HUE_FEATHER) * (
        1.0 - smoothstep(h, HUE_MAX - HUE_FEATHER, HUE_MAX + HUE_FEATHER)
    )
    w_s = smoothstep(s, SAT_MIN - SAT_FEATHER, SAT_MIN + SAT_FEATHER)
    w_v = smoothstep(v, VAL_MIN - VAL_FEATHER, VAL_MIN + VAL_FEATHER)
    w = (w_h * w_s * w_v).astype(np.float32)
    w[alpha <= ALPHA_MIN] = 0.0
    return w


def load_rgba_float(path):
    arr = np.asarray(Image.open(path).convert("RGBA"), dtype=np.float32) / 255.0
    return arr[..., :3], arr[..., 3]


# --------------------------------------------------------------------------- #
# Componentes conexos (SciPy se houver; senão, flood fill em Python puro)
# --------------------------------------------------------------------------- #
try:  # pragma: no cover - depende do ambiente
    from scipy import ndimage as _ndi

    def label_components(mask):
        labels, n = _ndi.label(mask, structure=np.ones((3, 3), dtype=int))
        return labels.astype(np.int32), int(n)

except ImportError:  # pragma: no cover

    def label_components(mask):
        h, w = mask.shape
        m = mask.tolist()
        lab = [[0] * w for _ in range(h)]
        n = 0
        ys, xs = np.nonzero(mask)
        for y0, x0 in zip(ys.tolist(), xs.tolist()):
            if lab[y0][x0]:
                continue
            n += 1
            lab[y0][x0] = n
            stack = [(y0, x0)]
            while stack:
                y, x = stack.pop()
                for yy in (y - 1, y, y + 1):
                    if yy < 0 or yy >= h:
                        continue
                    row_m, row_l = m[yy], lab[yy]
                    for xx in (x - 1, x, x + 1):
                        if 0 <= xx < w and row_m[xx] and not row_l[xx]:
                            row_l[xx] = n
                            stack.append((yy, xx))
        return np.array(lab, dtype=np.int32), n


def component_stats(labels, n):
    flat = labels.ravel()
    area = np.bincount(flat, minlength=n + 1).astype(np.float64)
    yy = np.repeat(np.arange(labels.shape[0], dtype=np.float64), labels.shape[1])
    cy = np.bincount(flat, weights=yy, minlength=n + 1)
    cy = np.divide(cy, area, out=np.zeros_like(cy), where=area > 0)
    return area, cy


# --------------------------------------------------------------------------- #
# Rampa luminância -> RGB apagado
# --------------------------------------------------------------------------- #
def build_ramp(key, colors):
    """Rampa (percentil 0..1 -> RGB 0..1) a partir de pares (chave, cor).

    Ordena por `key`, divide em bins de mesmo tamanho e usa a mediana de cada bin;
    depois suaviza levemente. Retorna função t -> (N,3).
    """
    n = len(key)
    k = int(max(2, min(RAMP_SIZE, n // 8)))
    order = np.argsort(key, kind="stable")
    chunks = np.array_split(colors[order], k)
    med = np.stack([np.median(c, axis=0) for c in chunks]).astype(np.float64)

    win = 5
    pad = np.pad(med, ((win // 2, win // 2), (0, 0)), mode="edge")
    kernel = np.ones(win) / win
    med = np.stack([np.convolve(pad[:, c], kernel, mode="valid") for c in range(3)], axis=1)

    grid = np.linspace(0.0, 1.0, k)

    def ramp(t):
        t = np.clip(t, 0.0, 1.0)
        return np.stack([np.interp(t, grid, med[:, c]) for c in range(3)], axis=-1)

    return ramp


def compute_unlit_ramp():
    """Compara frame 18 (aceso) com frame 01 (apagado) e devolve a rampa malva."""
    lit_rgb, lit_a = load_rgba_float(FRAME_ACESO)
    unl_rgb, unl_a = load_rgba_float(FRAME_APAGADO)

    if unl_rgb.shape != lit_rgb.shape:
        h, w = lit_rgb.shape[:2]
        unl_img = Image.open(FRAME_APAGADO).convert("RGBA").resize((w, h), Image.NEAREST)
        unl = np.asarray(unl_img, dtype=np.float32) / 255.0
        unl_rgb, unl_a = unl[..., :3], unl[..., 3]

    # Abdômen aceso no frame 18 (núcleo da máscara + sanidade espacial).
    w_lit = amber_weight(lit_rgb, lit_a)
    core = (w_lit > 0.5) & (lit_a >= 0.95)
    labels, n = label_components(core)
    if n == 0:
        raise RuntimeError("Nenhum pixel âmbar encontrado em lume-acendimento-18.png")
    area, _ = component_stats(labels, n)
    area[0] = 0
    keep = area >= max(MIN_COMP_AREA, MIN_COMP_REL * area.max())
    keep[0] = False
    lit_mask = keep[labels]

    # Modo pareado: mesmos pixels no frame 01 (apagado), que não podem ser âmbar.
    w_unl = amber_weight(unl_rgb, unl_a)
    paired = lit_mask & (unl_a >= 0.95) & (w_unl < 0.5)
    if paired.sum() >= MIN_RAMP_PIXELS and paired.sum() >= 0.6 * lit_mask.sum():
        key = luminance(lit_rgb[paired])          # luminância do aceso...
        colors = unl_rgb[paired]                  # ...-> cor do apagado no mesmo pixel
        print(f"[rampa] modo pareado: {int(paired.sum())} px (frame 18 -> frame 01)")
        return build_ramp(key, colors)

    # Reserva: acha o malva do frame 01 perto da região do abdômen aceso.
    print("[rampa] frames não pareáveis; usando detecção de malva no frame 01")
    ys, xs = np.nonzero(lit_mask)
    pad = 8
    y0, y1 = max(0, ys.min() - pad), ys.max() + pad + 1
    x0, x1 = max(0, xs.min() - pad), xs.max() + pad + 1
    h, s, v = rgb_to_hsv(unl_rgb)
    mauve = (h >= MAUVE_HUE[0]) & (h <= MAUVE_HUE[1]) & (s > MAUVE_SAT_MIN) & (v > VAL_MIN) & (unl_a >= 0.95)
    region = np.zeros_like(mauve)
    region[y0:y1, x0:x1] = True
    mauve &= region
    if mauve.sum() < MIN_RAMP_PIXELS:
        raise RuntimeError("Não foi possível amostrar o abdômen malva em lume-acendimento-01.png")
    print(f"[rampa] malva amostrado: {int(mauve.sum())} px")
    return build_ramp(luminance(unl_rgb[mauve]), unl_rgb[mauve])


# --------------------------------------------------------------------------- #
# Remapeamento do mascote
# --------------------------------------------------------------------------- #
def spatial_filter(weights, alpha):
    """Zera pesos fora dos componentes plausíveis de abdômen, célula a célula."""
    H, W = weights.shape
    ch, cw = H // ROWS, W // COLS
    for r in range(ROWS):
        for c in range(COLS):
            sl = (slice(r * ch, (r + 1) * ch), slice(c * cw, (c + 1) * cw))
            wc = weights[sl]
            cand = wc > CAND_THRESHOLD
            if not cand.any():
                wc[:] = 0
                continue
            labels, n = label_components(cand)
            area, cy = component_stats(labels, n)
            area[0] = 0
            big = int(np.argmax(area))

            ay = np.nonzero((alpha[sl] > 0.06).any(axis=1))[0]
            top, height = (ay.min(), max(1, ay.max() - ay.min() + 1)) if len(ay) else (0, ch)
            rel_y = (cy - top) / height

            keep = np.zeros(n + 1, dtype=bool)
            ok = (area >= MIN_COMP_AREA) & (area >= MIN_COMP_REL * area[big]) & (rel_y >= LOWER_FRAC)
            keep |= ok
            keep[big] = True
            keep[0] = False
            wc[~keep[labels]] = 0.0


def remap_sheet(arr_u8, ramp):
    rgb = arr_u8[..., :3].astype(np.float32) / 255.0
    alpha = arr_u8[..., 3].astype(np.float32) / 255.0

    weights = amber_weight(rgb, alpha)
    spatial_filter(weights, alpha)

    core = weights > 0.5
    if not core.any():
        raise RuntimeError("Nenhum pixel de abdômen aceso encontrado no mascote")

    # Casamento de quantis: percentil de luminância do pixel no mascote -> rampa.
    lum_core = luminance(rgb[core])
    qs = np.quantile(lum_core, np.linspace(0.0, 1.0, QUANT_POINTS))
    qs = np.maximum.accumulate(qs) + np.arange(QUANT_POINTS) * 1e-9
    tgrid = np.linspace(0.0, 1.0, QUANT_POINTS)

    sel = weights > 0.004
    ys, xs = np.nonzero(sel)
    src = rgb[ys, xs]
    t = np.interp(luminance(src), qs, tgrid)
    mapped = ramp(t).astype(np.float32)
    w = weights[ys, xs][:, None]
    blended = src * (1.0 - w) + mapped * w

    out = arr_u8.copy()
    out[ys, xs, :3] = np.clip(np.rint(blended * 255.0), 0, 255).astype(np.uint8)
    # alfa permanece exatamente igual (out[..., 3] não foi tocado)
    print(f"[mascote] {int(core.sum())} px núcleo / {len(ys)} px com peso > 0 remapeados")
    return out


# --------------------------------------------------------------------------- #
# GIF de pulso
# --------------------------------------------------------------------------- #
def make_gif(aceso_u8, apagado_u8):
    H, W = aceso_u8.shape[:2]
    ch, cw = H // ROWS, W // COLS

    non_empty = [c for c in range(COLS) if aceso_u8[0:ch, c * cw:(c + 1) * cw, 3].max() > 0]
    cells_on = [aceso_u8[0:ch, c * cw:(c + 1) * cw].astype(np.float32) for c in non_empty]
    cells_off = [apagado_u8[0:ch, c * cw:(c + 1) * cw].astype(np.float32) for c in non_empty]
    n_idle = len(cells_on)
    bg = np.array(GIF_BG, dtype=np.float32)

    def compose(i, k):
        on, off = cells_on[i % n_idle], cells_off[i % n_idle]
        rgb = off[..., :3] * (1.0 - k) + on[..., :3] * k
        a = (on[..., 3] / 255.0)[..., None]
        comp = rgb * a + bg * (1.0 - a)
        img = Image.fromarray(np.clip(np.rint(comp), 0, 255).astype(np.uint8))
        if GIF_SCALE != 1:
            img = img.resize((img.width * GIF_SCALE, img.height * GIF_SCALE), Image.NEAREST)
        return img

    def pulse(i):
        return 0.5 - 0.5 * np.cos(2.0 * np.pi * i / GIF_PULSE_PERIOD)

    rgb_frames = [compose(i, float(pulse(i))) for i in range(GIF_FRAMES)]

    # Paleta global (evita cintilação entre quadros): montagem de apagado/meio/aceso.
    probe = [compose(i, k) for i in range(n_idle) for k in (0.0, 0.5, 1.0)][::2]
    probe += [compose(i, 0.5) for i in range(0, n_idle, 2)] + [compose(i, 1.0) for i in range(0, n_idle, 2)]
    sheet = Image.new("RGB", (probe[0].width * len(probe), probe[0].height))
    for j, im in enumerate(probe):
        sheet.paste(im, (j * im.width, 0))
    quant_enum = getattr(Image, "Quantize", Image)
    dither_enum = getattr(Image, "Dither", Image)
    pal = sheet.quantize(colors=256, method=quant_enum.MEDIANCUT, dither=dither_enum.NONE)

    frames = [im.quantize(palette=pal, dither=dither_enum.NONE) for im in rgb_frames]
    frames[0].save(
        OUT_GIF,
        save_all=True,
        append_images=frames[1:],
        duration=GIF_DURATION_MS,
        loop=0,
        disposal=1,
        optimize=False,
    )
    print(f"[gif] {len(frames)} quadros, {GIF_DURATION_MS} ms/quadro -> {OUT_GIF.name}")


# --------------------------------------------------------------------------- #
def main():
    for p in (FRAME_APAGADO, FRAME_ACESO, SHEET):
        if not p.exists():
            raise FileNotFoundError(f"Arquivo de entrada não encontrado: {p}")

    ramp = compute_unlit_ramp()

    sheet = Image.open(SHEET).convert("RGBA")
    if sheet.size != (1536, 2288):
        print(f"[aviso] tamanho inesperado {sheet.size}; esperado (1536, 2288)")
    aceso = np.asarray(sheet, dtype=np.uint8).copy()

    apagado = remap_sheet(aceso, ramp)
    Image.fromarray(apagado).save(OUT_PNG, optimize=True)
    print(f"[png] salvo: {OUT_PNG.name}")

    make_gif(aceso, apagado)


if __name__ == "__main__":
    main()
