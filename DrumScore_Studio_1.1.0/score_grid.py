"""Validated drum grid -> MusicXML. Internal pitches use General MIDI numbers."""
from xml.etree import ElementTree as ET

DRUMS = {
    'crash': ('Crash Cymbal', 49, 'A', 5, 'x'),
    'ride': ('Ride Cymbal', 51, 'F', 5, 'x'),
    'hihat': ('Closed Hi-Hat', 42, 'G', 5, 'x'),
    'hihat_open': ('Open Hi-Hat', 46, 'G', 5, 'x'),
    'hihat_pedal': ('Pedal Hi-Hat', 44, 'D', 4, 'x'),
    'tom_high': ('High Tom', 50, 'E', 5, None),
    'tom_mid': ('Mid Tom', 47, 'D', 5, None),
    'snare': ('Snare Drum', 38, 'C', 5, None),
    'sidestick': ('Side Stick', 37, 'C', 5, 'x'),
    'tom_low': ('Low Tom', 43, 'A', 4, None),
    'kick': ('Bass Drum', 36, 'F', 4, None),
}


def validate_config(config=None):
    c = dict(config or {})
    try:
        numerator, denominator = map(int, str(c.get('meter', '4/4')).split('/'))
        subdivision = int(c.get('subdivision', 8))
        bpm = int(c.get('bpm', 120))
    except (ValueError, TypeError):
        raise ValueError('Revisá el tempo, el compás y la subdivisión.')
    if not 1 <= numerator <= 12 or denominator not in (4, 8):
        raise ValueError('Usá un compás de 1 a 12 tiempos, con denominador 4 u 8.')
    if subdivision not in (8, 12, 16, 24, 32) or numerator * subdivision % denominator:
        raise ValueError('La subdivisión elegida no completa este compás.')
    if not 30 <= bpm <= 280:
        raise ValueError('El tempo debe estar entre 30 y 280 BPM.')
    return {'meter': f'{numerator}/{denominator}', 'subdivision': subdivision, 'bpm': bpm,
            'title': str(c.get('title') or 'Partitura de batería').strip()[:160],
            'slotsPerMeasure': numerator * subdivision // denominator}


def compile_grid(grid, config=None):
    c = validate_config(config)
    if not isinstance(grid, list) or not 1 <= len(grid) <= 256:
        raise ValueError('La partitura debe tener entre 1 y 256 compases.')
    n, d = map(int, c['meter'].split('/'))
    sub = c['subdivision']
    divisions = 24
    duration = divisions * 4 // sub
    is_triplet = sub in (12, 24)
    note_type = {8: 'eighth', 12: 'eighth', 16: '16th', 24: '16th', 32: '32nd'}[sub]
    root = ET.Element('score-partwise', version='4.0')
    ET.SubElement(ET.SubElement(root, 'work'), 'work-title').text = c['title']
    part = ET.SubElement(ET.SubElement(root, 'part-list'), 'score-part', id='P1')
    ET.SubElement(part, 'part-name').text = 'Batería'
    for key, (name, midi, *_) in DRUMS.items():
        inst = ET.SubElement(part, 'score-instrument', id=f'P1-I{midi}')
        ET.SubElement(inst, 'instrument-name').text = name
    for name, midi, *_ in DRUMS.values():
        inst = ET.SubElement(part, 'midi-instrument', id=f'P1-I{midi}')
        ET.SubElement(inst, 'midi-channel').text = '10'
        ET.SubElement(inst, 'midi-unpitched').text = str(midi + 1)
    part = ET.SubElement(root, 'part', id='P1')
    stats = {'Bass Drum': 0, 'Snare Drum': 0, 'Closed Hi-Hat': 0, 'Crash Cymbal': 0, 'Toms': 0}
    normalized = []
    for index, entry in enumerate(grid):
        if not isinstance(entry, dict) or not isinstance(entry.get('slots'), list) or len(entry['slots']) != c['slotsPerMeasure']:
            raise ValueError(f'El compás {index + 1} debe contener {c["slotsPerMeasure"]} casillas.')
        measure = ET.SubElement(part, 'measure', number=str(index + 1))
        if index == 0:
            attributes = ET.SubElement(measure, 'attributes')
            ET.SubElement(attributes, 'divisions').text = str(divisions)
            time = ET.SubElement(attributes, 'time')
            ET.SubElement(time, 'beats').text = str(n)
            ET.SubElement(time, 'beat-type').text = str(d)
            clef = ET.SubElement(attributes, 'clef')
            ET.SubElement(clef, 'sign').text = 'percussion'
            direction = ET.SubElement(measure, 'direction', placement='above')
            met = ET.SubElement(ET.SubElement(direction, 'direction-type'), 'metronome')
            ET.SubElement(met, 'beat-unit').text = 'quarter'
            ET.SubElement(met, 'per-minute').text = str(c['bpm'])
            ET.SubElement(direction, 'sound', tempo=str(c['bpm']))
        slots = []
        for slot_index, slot in enumerate(entry['slots']):
            instruments = slot.get('instruments') if isinstance(slot, dict) else None
            if not isinstance(instruments, list) or any(not isinstance(k, str) or k not in DRUMS for k in instruments):
                raise ValueError('La cuadrícula contiene un instrumento desconocido.')
            instruments = list(dict.fromkeys(instruments))
            slots.append({'slot': slot_index, 'instruments': instruments})
            for chord_index, key in enumerate(instruments or [None]):
                note = ET.SubElement(measure, 'note')
                if chord_index: ET.SubElement(note, 'chord')
                if key:
                    name, midi, step, octave, head = DRUMS[key]
                    unpitched = ET.SubElement(note, 'unpitched')
                    ET.SubElement(unpitched, 'display-step').text = step
                    ET.SubElement(unpitched, 'display-octave').text = str(octave)
                    category = 'Toms' if key.startswith('tom_') else ('Closed Hi-Hat' if key.startswith('hihat') else ('Crash Cymbal' if key in ('crash', 'ride') else ('Snare Drum' if key == 'sidestick' else name)))
                    stats[category] = stats.get(category, 0) + 1
                else: ET.SubElement(note, 'rest')
                ET.SubElement(note, 'duration').text = str(duration)
                if key: ET.SubElement(note, 'instrument', id=f'P1-I{midi}')
                ET.SubElement(note, 'voice').text = '1'
                ET.SubElement(note, 'type').text = note_type
                if is_triplet:
                    tm = ET.SubElement(note, 'time-modification')
                    ET.SubElement(tm, 'actual-notes').text = '3'
                    ET.SubElement(tm, 'normal-notes').text = '2'
                    ET.SubElement(tm, 'normal-type').text = note_type
                if key:
                    ET.SubElement(note, 'stem').text = 'up'
                    if head: ET.SubElement(note, 'notehead').text = head
        normalized.append({'measure': index + 1, 'slots': slots})
    xml = ET.tostring(root, encoding='unicode', xml_declaration=True)
    return {'success': True, 'musicXml': xml, 'config': c, 'grid': normalized, 'stats': stats,
            'measuresCount': len(grid), 'totalNotes': sum(stats.values())}
