"""Assisted OMR for clean, single-instrument, five-line drum staves.

Geometry estimates onsets on the user-selected grid; it is not a general OCR
engine. Ambiguous measures are returned for manual review, never filled with
an invented previous pattern or a fabricated detected tempo.
"""
import base64
import io
import warnings
import numpy as np
from PIL import Image, ImageDraw, ImageOps, UnidentifiedImageError
from scipy import ndimage
from score_grid import compile_grid, validate_config, DRUMS


class DrumOMR:
    def process_image(self, image_bytes, bpm=None, config=None):
        config = dict(config or {})
        if bpm is not None: config['bpm'] = bpm
        c = validate_config(config)
        try:
            with warnings.catch_warnings():
                warnings.simplefilter('error', Image.DecompressionBombWarning)
                img = ImageOps.exif_transpose(Image.open(io.BytesIO(image_bytes)))
                if img.width * img.height > 20_000_000:
                    raise ValueError('La imagen supera los 20 megapíxeles. Reducí su tamaño.')
                if 'A' in img.getbands():
                    background = Image.new('RGBA', img.size, 'white')
                    background.alpha_composite(img.convert('RGBA'))
                    img = background.convert('RGB')
                else: img = img.convert('RGB')
                img.thumbnail((2000, 2400), Image.Resampling.LANCZOS)
        except (UnidentifiedImageError, Image.DecompressionBombError, Image.DecompressionBombWarning):
            raise ValueError('No se pudo abrir la imagen. Usá PNG, JPG, WEBP o BMP de hasta 20 megapíxeles.')
        binary = self._binary(img)
        angle = 0.0
        staves = self._detect_all_staves(binary)
        if not staves:
            img, angle = self._deskew(img)
            binary = self._binary(img)
            staves = self._detect_all_staves(binary)
        if not staves:
            raise ValueError('No se encontró un pentagrama de cinco líneas. Recortá la partitura y usá una imagen más nítida.')
        measures = self._detect_all_measures(binary, staves)
        if not measures: raise ValueError('No se pudieron separar los compases. Probá recortar un solo renglón.')
        if len(measures) > 256: raise ValueError('Dividí la imagen en páginas de hasta 256 compases.')
        grid, notes, review = self._scan_measures(binary, staves, measures, c['slotsPerMeasure'])
        if not notes:
            raise ValueError('Se encontró el pentagrama, pero no se distinguieron notas. Probá una imagen más clara.')
        result = compile_grid(grid, c)
        draw = ImageDraw.Draw(img)
        for m in measures:
            top, bottom = m['lines'][0] - m['spacing'] * 2, m['lines'][-1] + m['spacing']
            draw.rectangle((m['x_left'], max(0, top), m['x_right'], min(img.height-1, bottom)), outline='#0284c7', width=1)
        colors = {'kick':'#059669','snare':'#dc2626','hihat':'#ca8a04','crash':'#ea580c'}
        for note in notes:
            x, y = note['x'], note['y']
            draw.ellipse((x-6,y-6,x+6,y+6), outline=colors.get(note['id'], '#9333ea'), width=2)
        out = io.BytesIO()
        img.save(out, format='PNG')
        result.update({'annotatedImage': 'data:image/png;base64,' + base64.b64encode(out.getvalue()).decode(),
                       'deskewAngle': round(angle, 2), 'systemsCount': len(staves),
                       'bpmSource': 'manual' if 'bpm' in config else 'default',
                       'reviewMeasures': review,
                       'warnings': ['Revisá instrumentos, silencios y tiempos en la cuadrícula. El tempo y el compás son los que elegiste; no se leen del texto.']})
        if review:
            result['warnings'].append('Revisá especialmente los compases ' + ', '.join(map(str, review)) + ': la posición rítmica es aproximada o no se reconocieron golpes.')
        return result

    def _otsu_threshold(self, arr):
        hist = np.bincount(arr.ravel(), minlength=256).astype(np.float64)
        total = float(arr.size)
        left_count = np.cumsum(hist)
        right_count = total - left_count
        left_sum = np.cumsum(hist * np.arange(256, dtype=np.float64))
        valid = (left_count > 0) & (right_count > 0)
        variance = np.zeros(256, dtype=np.float64)
        variance[valid] = (left_sum[-1] * left_count[valid] - left_sum[valid] * total) ** 2 / (left_count[valid] * right_count[valid])
        return min(210, max(85, int(np.argmax(variance)) + 8))

    def _binary(self, img):
        arr = np.array(ImageOps.grayscale(img))
        return (arr < self._otsu_threshold(arr)).astype(np.uint8)

    def _deskew(self, img):
        small = img.copy()
        small.thumbnail((1000, 1000))
        source = self._binary(small)
        def score(angle):
            rotated = ndimage.rotate(source, angle, reshape=False, order=0, cval=0)
            rows = rotated.sum(axis=1).astype(float)
            return float(np.sum(rows * rows))
        angles = np.arange(-7, 7.01, 0.5)
        best = max(angles, key=score)
        best = max(np.arange(best-0.4, best+0.41, 0.1), key=score)
        if abs(best) < 0.08 or score(best) < score(0) * 1.12: return img, 0.0
        return img.rotate(float(best), resample=Image.Resampling.BICUBIC, expand=True, fillcolor='white'), float(best)

    def _detect_all_staves(self, binary):
        h, w = binary.shape
        k_len = max(12, int(w * 0.06))
        opened = ndimage.binary_opening(binary, structure=np.ones((1, k_len)))
        row_sums = opened.sum(axis=1)
        thresh = max(w * 0.25, 20)
        rows = np.flatnonzero(row_sums >= thresh)
        if len(rows) < 5:
            rows = np.flatnonzero(row_sums >= max(w * 0.15, 15))
        clusters = []
        for y in rows:
            if not clusters or y - clusters[-1][-1] > 2: clusters.append([y])
            else: clusters[-1].append(y)
        centers = [int(round(np.mean(x))) for x in clusters]
        staves = []
        i = 0
        while i <= len(centers) - 5:
            lines = centers[i:i+5]
            diffs = np.diff(lines)
            spacing = float(np.mean(diffs))
            if 4 <= spacing <= 60 and np.std(diffs) <= max(0.85, spacing*0.14):
                staves.append({'lines': lines, 'spacing': spacing})
                i += 5
            else: i += 1
        return staves

    def _detect_all_measures(self, binary, staves):
        measures = []
        for system, st in enumerate(staves):
            top, bottom = st['lines'][0], st['lines'][-1]
            spacing = st['spacing']
            xs = np.flatnonzero(binary[top])
            if not len(xs): continue
            left, right = int(xs[0]), int(xs[-1])
            projection = ndimage.maximum_filter1d(binary[top:bottom+1], size=3, axis=1).sum(axis=0)
            candidates = []
            for x in range(left, right+1):
                if projection[x] < (bottom-top+1)*0.85: continue
                above = binary[max(0, int(top-1.5*spacing)):max(0,top-3), max(0,x-1):x+2].sum()
                if above > 2: continue
                if not candidates or x-candidates[-1][-1] > spacing*0.75: candidates.append([x])
                else: candidates[-1].append(x)
            bars = [int(round(np.mean(c))) for c in candidates]
            if not bars or bars[0]-left > spacing*4: bars.insert(0, left)
            if right-bars[-1] > spacing*2: bars.append(right)
            for x1, x2 in zip(bars, bars[1:]):
                # Discard the clef/time-signature prefix, not a musical measure.
                if x2-x1 < spacing*4: continue
                measures.append({**st, 'system_index':system, 'x_left':x1, 'x_right':x2, 'measure':len(measures)+1})
        return measures

    def _noteheads(self, binary, st):
        spacing = st['spacing']
        y0 = max(0, int(st['lines'][0] - 2*spacing))
        y1 = min(binary.shape[0], int(st['lines'][-1] + spacing))
        crop = binary[y0:y1].astype(bool)
        horizontal = ndimage.binary_opening(ndimage.binary_dilation(crop, structure=np.ones((3,1), bool)), structure=np.ones((1, max(10,int(spacing*3))), bool))
        vertical = ndimage.binary_opening(ndimage.binary_dilation(crop, structure=np.ones((1,3), bool)), structure=np.ones((max(10,int(spacing*1.2)),1), bool))
        clean = crop & ~horizontal & ~vertical
        clean = ndimage.binary_closing(clean, structure=np.ones((5,1), bool))
        labels, count = ndimage.label(clean, structure=np.ones((3,3), bool))
        heads = []
        for number, slices in enumerate(ndimage.find_objects(labels), 1):
            if slices is None: continue
            ys, xs = slices
            width, height = xs.stop-xs.start, ys.stop-ys.start
            mask = labels[slices] == number
            area = int(mask.sum())
            if not (spacing*0.28 <= width <= spacing*1.25 and spacing*0.23 <= height <= spacing*1.1): continue
            if area < max(7, spacing*spacing*0.075): continue
            cy, cx = ndimage.center_of_mass(mask)
            heads.append({'x':xs.start+float(cx), 'y':y0+ys.start+float(cy), 'area':area})
        return heads

    def _classify(self, y, st):
        pos = (y - st['lines'][0])/st['spacing']
        # Common drum notation; other conventions require correction in the editor.
        bands = [(-1.5,'crash'),(-0.5,'hihat'),(0,'ride'),(0.5,'tom_high'),
                 (1,'tom_mid'),(1.5,'snare'),(2.5,'tom_low'),(3,'tom_low'),(3.5,'kick'),(4,'kick'),(4.5,'hihat_pedal')]
        target, instrument = min(bands, key=lambda b: abs(b[0]-pos))
        return instrument if abs(target-pos) <= 0.24 else None

    def _scan_measures(self, binary, staves, measures, slots):
        by_system = [self._noteheads(binary, st) for st in staves]
        grid, notes, review = [], [], []
        for m in measures:
            heads = [h for h in by_system[m['system_index']] if m['x_left']+m['spacing']*0.5 < h['x'] < m['x_right']-m['spacing']*0.5]
            heads = [{**h,'id':self._classify(h['y'],m)} for h in heads]
            heads = [h for h in heads if h['id']]
            groups = []
            for head in sorted(heads, key=lambda h:h['x']):
                if not groups or head['x']-np.mean([h['x'] for h in groups[-1]]) > m['spacing']*0.6: groups.append([head])
                else: groups[-1].append(head)
            measure_slots = [{'slot':i,'instruments':[]} for i in range(slots)]
            if len(groups) != slots: review.append(m['measure'])
            for index, group in enumerate(groups):
                x = float(np.mean([h['x'] for h in group]))
                slot = index if len(groups)==slots else int(np.floor((x-m['x_left'])/(m['x_right']-m['x_left'])*slots))
                slot = max(0,min(slots-1,slot))
                for head in group:
                    if head['id'] not in measure_slots[slot]['instruments']:
                        measure_slots[slot]['instruments'].append(head['id'])
                        notes.append({**head,'measure':m['measure'],'slot':slot})
            grid.append({'measure':m['measure'],'slots':measure_slots})
        return grid, notes, review
