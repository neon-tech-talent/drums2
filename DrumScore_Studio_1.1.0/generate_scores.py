# generate_scores.py
import os
from xml.sax.saxutils import escape

os.makedirs('assets/scores', exist_ok=True)

def note_xml(step, octave, duration, note_type, instrument_id, notehead=None, is_chord=False, stem="up", voice=1):
    chord_tag = "    <chord/>\n" if is_chord else ""
    head_tag = f"    <notehead>{notehead}</notehead>\n" if notehead else ""
    return f"""  <note>
{chord_tag}    <unpitched>
      <display-step>{step}</display-step>
      <display-octave>{octave}</display-octave>
    </unpitched>
    <duration>{duration}</duration>
    <instrument id="{instrument_id}"/>
    <voice>{voice}</voice>
    <type>{note_type}</type>
    <stem>{stem}</stem>
{head_tag}  </note>
"""

def rest_xml(duration, note_type, voice=1):
    return f"""  <note>
    <rest/>
    <duration>{duration}</duration>
    <voice>{voice}</voice>
    <type>{note_type}</type>
  </note>
"""

def make_musicxml(filename, title, tempo_bpm, measures_list):
    header = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE score-partwise PUBLIC "-//Recordare//DTD MusicXML 3.1 Partwise//EN" "http://www.musicxml.org/dtds/partwise.dtd">
<score-partwise version="3.1">
  <work>
    <work-title>{escape(str(title))}</work-title>
  </work>
  <part-list>
    <score-part id="P1">
      <part-name>Bateria</part-name>
      <score-instrument id="P1-I36"><instrument-name>Bass Drum</instrument-name></score-instrument>
      <score-instrument id="P1-I38"><instrument-name>Acoustic Snare</instrument-name></score-instrument>
      <score-instrument id="P1-I37"><instrument-name>Side Stick</instrument-name></score-instrument>
      <score-instrument id="P1-I42"><instrument-name>Closed Hi-Hat</instrument-name></score-instrument>
      <score-instrument id="P1-I46"><instrument-name>Open Hi-Hat</instrument-name></score-instrument>
      <score-instrument id="P1-I44"><instrument-name>Pedal Hi-Hat</instrument-name></score-instrument>
      <score-instrument id="P1-I49"><instrument-name>Crash Cymbal</instrument-name></score-instrument>
      <score-instrument id="P1-I51"><instrument-name>Ride Cymbal</instrument-name></score-instrument>
      <score-instrument id="P1-I50"><instrument-name>High Tom</instrument-name></score-instrument>
      <score-instrument id="P1-I47"><instrument-name>Mid Tom</instrument-name></score-instrument>
      <score-instrument id="P1-I43"><instrument-name>Low Tom</instrument-name></score-instrument>
      <midi-device id="P1-I36" port="1"></midi-device>
      <midi-instrument id="P1-I36"><midi-channel>10</midi-channel><midi-unpitched>37</midi-unpitched></midi-instrument>
      <midi-instrument id="P1-I38"><midi-channel>10</midi-channel><midi-unpitched>39</midi-unpitched></midi-instrument>
      <midi-instrument id="P1-I37"><midi-channel>10</midi-channel><midi-unpitched>38</midi-unpitched></midi-instrument>
      <midi-instrument id="P1-I42"><midi-channel>10</midi-channel><midi-unpitched>43</midi-unpitched></midi-instrument>
      <midi-instrument id="P1-I46"><midi-channel>10</midi-channel><midi-unpitched>47</midi-unpitched></midi-instrument>
      <midi-instrument id="P1-I44"><midi-channel>10</midi-channel><midi-unpitched>45</midi-unpitched></midi-instrument>
      <midi-instrument id="P1-I49"><midi-channel>10</midi-channel><midi-unpitched>50</midi-unpitched></midi-instrument>
      <midi-instrument id="P1-I51"><midi-channel>10</midi-channel><midi-unpitched>52</midi-unpitched></midi-instrument>
      <midi-instrument id="P1-I50"><midi-channel>10</midi-channel><midi-unpitched>51</midi-unpitched></midi-instrument>
      <midi-instrument id="P1-I47"><midi-channel>10</midi-channel><midi-unpitched>48</midi-unpitched></midi-instrument>
      <midi-instrument id="P1-I43"><midi-channel>10</midi-channel><midi-unpitched>44</midi-unpitched></midi-instrument>
    </score-part>
  </part-list>
  <part id="P1">
"""
    body = ""
    for idx, m_notes in enumerate(measures_list):
        m_num = idx + 1
        body += f'    <measure number="{m_num}">\n'
        if m_num == 1:
            body += f"""      <attributes>
        <divisions>4</divisions>
        <key><fifths>0</fifths></key>
        <time><beats>4</beats><beat-type>4</beat-type></time>
        <clef><sign>percussion</sign><line>2</line></clef>
      </attributes>
      <direction placement="above">
        <direction-type><metronome><beat-unit>quarter</beat-unit><per-minute>{tempo_bpm}</per-minute></metronome></direction-type>
        <sound tempo="{tempo_bpm}"/>
      </direction>
"""
        body += m_notes
        body += "    </measure>\n"

    footer = """  </part>
</score-partwise>"""
    
    path = os.path.join('assets/scores', filename)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(header + body + footer)
    print(f"Generated {path} ({os.path.getsize(path)} bytes)")

# 1. Classic Rock 4/4 Beat (4 bars: 3 groove + 1 fill + resolution)
def rock_measure(with_kick3_and=False):
    s = ""
    # Beat 1: Kick + HiHat
    s += note_xml("G", 5, 2, "eighth", "P1-I42", "cross")
    s += note_xml("F", 4, 2, "eighth", "P1-I36", None, is_chord=True, stem="down")
    # Beat 1&: HiHat
    s += note_xml("G", 5, 2, "eighth", "P1-I42", "cross")
    # Beat 2: Snare + HiHat
    s += note_xml("G", 5, 2, "eighth", "P1-I42", "cross")
    s += note_xml("C", 5, 2, "eighth", "P1-I38", None, is_chord=True)
    # Beat 2&: HiHat
    s += note_xml("G", 5, 2, "eighth", "P1-I42", "cross")
    # Beat 3: Kick + HiHat
    s += note_xml("G", 5, 2, "eighth", "P1-I42", "cross")
    s += note_xml("F", 4, 2, "eighth", "P1-I36", None, is_chord=True, stem="down")
    # Beat 3&: HiHat (+ Kick if variation)
    s += note_xml("G", 5, 2, "eighth", "P1-I42", "cross")
    if with_kick3_and:
        s += note_xml("F", 4, 2, "eighth", "P1-I36", None, is_chord=True, stem="down")
    # Beat 4: Snare + HiHat
    s += note_xml("G", 5, 2, "eighth", "P1-I42", "cross")
    s += note_xml("C", 5, 2, "eighth", "P1-I38", None, is_chord=True)
    # Beat 4&: HiHat
    s += note_xml("G", 5, 2, "eighth", "P1-I42", "cross")
    return s

def rock_fill():
    s = ""
    s += note_xml("G", 5, 2, "eighth", "P1-I42", "cross")
    s += note_xml("F", 4, 2, "eighth", "P1-I36", None, is_chord=True, stem="down")
    s += note_xml("G", 5, 2, "eighth", "P1-I42", "cross")
    s += note_xml("G", 5, 2, "eighth", "P1-I42", "cross")
    s += note_xml("C", 5, 2, "eighth", "P1-I38", None, is_chord=True)
    # Fill: 16th notes: Snare, Snare, High Tom, Mid Tom, Low Tom, Low Tom
    s += note_xml("C", 5, 1, "16th", "P1-I38", None)
    s += note_xml("C", 5, 1, "16th", "P1-I38", None)
    s += note_xml("E", 5, 1, "16th", "P1-I50", None)
    s += note_xml("E", 5, 1, "16th", "P1-I50", None)
    s += note_xml("D", 5, 1, "16th", "P1-I47", None)
    s += note_xml("D", 5, 1, "16th", "P1-I47", None)
    s += note_xml("A", 4, 1, "16th", "P1-I43", None)
    s += note_xml("A", 4, 1, "16th", "P1-I43", None)
    return s

def rock_resolution():
    s = ""
    s += note_xml("A", 5, 4, "quarter", "P1-I49", "cross")
    s += note_xml("F", 4, 4, "quarter", "P1-I36", None, is_chord=True, stem="down")
    s += rest_xml(4, "quarter")
    s += rest_xml(8, "half")
    return s

make_musicxml("rock_beat_4_4.musicxml", "Classic Rock Beat (120 BPM)", 120, [
    rock_measure(False),
    rock_measure(True),
    rock_measure(False),
    rock_fill(),
    rock_resolution()
])

# 2. Funk 16th Groove (98 BPM)
def funk_groove_m1():
    s = ""
    # 1e&a (HiHat continuous 16ths: 1=Kick+HH, e=HH, &=HH, a=Kick+HH)
    s += note_xml("G", 5, 1, "16th", "P1-I42", "cross")
    s += note_xml("F", 4, 1, "16th", "P1-I36", None, is_chord=True, stem="down")
    s += note_xml("G", 5, 1, "16th", "P1-I42", "cross")
    s += note_xml("G", 5, 1, "16th", "P1-I42", "cross")
    s += note_xml("G", 5, 1, "16th", "P1-I42", "cross")
    s += note_xml("F", 4, 1, "16th", "P1-I36", None, is_chord=True, stem="down")
    
    # 2e&a (2=Snare+HH, e=SnareGhost, &=HH open, a=SnareGhost)
    s += note_xml("G", 5, 1, "16th", "P1-I42", "cross")
    s += note_xml("C", 5, 1, "16th", "P1-I38", None, is_chord=True)
    s += note_xml("C", 5, 1, "16th", "P1-I38", None)
    s += note_xml("G", 5, 1, "16th", "P1-I46", "circle-x")
    s += note_xml("C", 5, 1, "16th", "P1-I38", None)
    
    # 3e&a (3=Kick+HH, e=HH, &=Kick+HH, a=HH)
    s += note_xml("G", 5, 1, "16th", "P1-I42", "cross")
    s += note_xml("F", 4, 1, "16th", "P1-I36", None, is_chord=True, stem="down")
    s += note_xml("G", 5, 1, "16th", "P1-I42", "cross")
    s += note_xml("G", 5, 1, "16th", "P1-I42", "cross")
    s += note_xml("F", 4, 1, "16th", "P1-I36", None, is_chord=True, stem="down")
    s += note_xml("G", 5, 1, "16th", "P1-I42", "cross")

    # 4e&a (4=Snare+HH, e=SnareGhost, &=HH open, a=Kick)
    s += note_xml("G", 5, 1, "16th", "P1-I42", "cross")
    s += note_xml("C", 5, 1, "16th", "P1-I38", None, is_chord=True)
    s += note_xml("C", 5, 1, "16th", "P1-I38", None)
    s += note_xml("G", 5, 1, "16th", "P1-I46", "circle-x")
    s += note_xml("F", 4, 1, "16th", "P1-I36", None, stem="down")
    return s

make_musicxml("funk_groove_16th.musicxml", "Funk 16th-Note Groove (98 BPM)", 98, [
    funk_groove_m1(),
    funk_groove_m1(),
    funk_groove_m1(),
    funk_groove_m1()
])

# 3. Jazz Swing Ride (140 BPM)
def jazz_measure():
    s = ""
    # Beat 1: Ride quarter + light kick
    s += note_xml("F", 5, 4, "quarter", "P1-I51", "cross")
    s += note_xml("F", 4, 4, "quarter", "P1-I36", None, is_chord=True, stem="down")
    # Beat 2: Ride dotted-eighth + HiHat pedal + Ride 16th swing
    s += note_xml("F", 5, 3, "eighth", "P1-I51", "cross")
    s += note_xml("D", 4, 3, "eighth", "P1-I44", "cross", is_chord=True, stem="down")
    s += note_xml("F", 5, 1, "16th", "P1-I51", "cross")
    # Beat 3: Ride quarter + light snare comping
    s += note_xml("F", 5, 4, "quarter", "P1-I51", "cross")
    s += note_xml("C", 5, 4, "quarter", "P1-I38", None, is_chord=True)
    # Beat 4: Ride dotted-eighth + HiHat pedal + Ride 16th swing
    s += note_xml("F", 5, 3, "eighth", "P1-I51", "cross")
    s += note_xml("D", 4, 3, "eighth", "P1-I44", "cross", is_chord=True, stem="down")
    s += note_xml("F", 5, 1, "16th", "P1-I51", "cross")
    return s

make_musicxml("jazz_swing_ride.musicxml", "Jazz Swing & Ride Cymbal (140 BPM)", 140, [
    jazz_measure(),
    jazz_measure(),
    jazz_measure(),
    jazz_measure()
])

# 4. Metal Double Bass (160 BPM)
def metal_measure(bar_idx):
    s = ""
    for b in range(4):
        for sub in range(4):
            if sub == 0:
                if b == 0 and bar_idx == 0:
                    s += note_xml("A", 5, 1, "16th", "P1-I49", "cross")
                elif b == 1 or b == 3:
                    s += note_xml("C", 5, 1, "16th", "P1-I38", None)
                else:
                    s += note_xml("F", 5, 1, "16th", "P1-I51", "cross")
                s += note_xml("F", 4, 1, "16th", "P1-I36", None, is_chord=True, stem="down")
            elif sub == 2:
                s += note_xml("F", 5, 1, "16th", "P1-I51", "cross")
                s += note_xml("F", 4, 1, "16th", "P1-I36", None, is_chord=True, stem="down")
            else:
                s += note_xml("F", 4, 1, "16th", "P1-I36", None, stem="down")
    return s

make_musicxml("metal_double_bass.musicxml", "Heavy Metal Double Bass (160 BPM)", 160, [
    metal_measure(0),
    metal_measure(1),
    metal_measure(2),
    metal_measure(3)
])

# 5. Latin Bossa Nova (130 BPM)
def bossa_measure():
    s = ""
    # 1: Ride + Kick + SnareSideStick
    s += note_xml("F", 5, 2, "eighth", "P1-I51", "cross")
    s += note_xml("F", 4, 2, "eighth", "P1-I36", None, is_chord=True, stem="down")
    s += note_xml("C", 5, 2, "eighth", "P1-I37", "cross", is_chord=True)
    # 1&: Ride + Kick
    s += note_xml("F", 5, 1, "16th", "P1-I51", "cross")
    s += note_xml("F", 4, 1, "16th", "P1-I36", None, stem="down")
    # 2: Ride + Kick + HiHatPedal
    s += note_xml("F", 5, 2, "eighth", "P1-I51", "cross")
    s += note_xml("F", 4, 2, "eighth", "P1-I36", None, is_chord=True, stem="down")
    s += note_xml("D", 4, 2, "eighth", "P1-I44", "cross", is_chord=True, stem="down")
    # 2&: Ride + SnareSideStick
    s += note_xml("F", 5, 1, "16th", "P1-I51", "cross")
    s += note_xml("C", 5, 1, "16th", "P1-I37", "cross", is_chord=True)
    # 3: Ride + Kick
    s += note_xml("F", 5, 2, "eighth", "P1-I51", "cross")
    s += note_xml("F", 4, 2, "eighth", "P1-I36", None, is_chord=True, stem="down")
    # 3&: Ride + Kick + SnareSideStick
    s += note_xml("F", 5, 2, "eighth", "P1-I51", "cross")
    s += note_xml("F", 4, 2, "eighth", "P1-I36", None, is_chord=True, stem="down")
    s += note_xml("C", 5, 2, "eighth", "P1-I37", "cross", is_chord=True)
    # 4: Ride + Kick + HiHatPedal
    s += note_xml("F", 5, 2, "eighth", "P1-I51", "cross")
    s += note_xml("F", 4, 2, "eighth", "P1-I36", None, is_chord=True, stem="down")
    s += note_xml("D", 4, 2, "eighth", "P1-I44", "cross", is_chord=True, stem="down")
    # 4&: Ride
    s += note_xml("F", 5, 2, "eighth", "P1-I51", "cross")
    return s

make_musicxml("latin_bossa_nova.musicxml", "Latin Bossa Nova (130 BPM)", 130, [
    bossa_measure(),
    bossa_measure(),
    bossa_measure(),
    bossa_measure()
])

# 6. Drum Rudiments & Fills (110 BPM)
def rudiments_measure1():
    s = ""
    for _ in range(16):
        s += note_xml("C", 5, 1, "16th", "P1-I38", None)
    return s

def rudiments_measure2():
    s = ""
    for group in range(4):
        s += note_xml("C", 5, 1, "16th", "P1-I38", None)
        s += note_xml("C", 5, 1, "16th", "P1-I38", None)
        s += note_xml("C", 5, 1, "16th", "P1-I38", None)
        s += note_xml("C", 5, 1, "16th", "P1-I38", None)
    return s

def rudiments_measure3():
    s = ""
    for _ in range(4): s += note_xml("C", 5, 1, "16th", "P1-I38", None)
    for _ in range(4): s += note_xml("E", 5, 1, "16th", "P1-I50", None)
    for _ in range(4): s += note_xml("D", 5, 1, "16th", "P1-I47", None)
    for _ in range(4): s += note_xml("A", 4, 1, "16th", "P1-I43", None)
    return s

def rudiments_measure4():
    s = ""
    s += note_xml("A", 5, 4, "quarter", "P1-I49", "cross")
    s += note_xml("F", 4, 4, "quarter", "P1-I36", None, is_chord=True, stem="down")
    s += rest_xml(4, "quarter")
    s += rest_xml(8, "half")
    return s

make_musicxml("drum_rudiments_fills.musicxml", "Drum Rudiments & Tom Fills (110 BPM)", 110, [
    rudiments_measure1(),
    rudiments_measure2(),
    rudiments_measure3(),
    rudiments_measure4()
])

print("All drum preset MusicXML scores generated successfully!")
