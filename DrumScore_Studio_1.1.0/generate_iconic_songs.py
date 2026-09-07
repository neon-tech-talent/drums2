# generate_iconic_songs.py
import os
from generate_scores import note_xml, rest_xml, make_musicxml

# 1. Coldplay - Yellow (87 BPM, exactly as in PichuDrummer video _QKgxwz969Y)
# The verse pattern:
# Hi-hat 8th notes throughout
# Beat 1: Kick + Hi-Hat
# Beat 1&: Hi-Hat
# Beat 2: Snare + Hi-Hat
# Beat 2&: Kick + Hi-Hat (the classic Yellow groove syncopation)
# Beat 3: Kick + Hi-Hat
# Beat 3&: Hi-Hat
# Beat 4: Snare + Hi-Hat
# Beat 4&: Hi-Hat
def coldplay_verse():
    s = ""
    # 1: Kick + HiHat
    s += note_xml("G", 5, 2, "eighth", "P1-I42", "cross")
    s += note_xml("F", 4, 2, "eighth", "P1-I36", None, is_chord=True, stem="down")
    # 1&: HiHat
    s += note_xml("G", 5, 2, "eighth", "P1-I42", "cross")
    # 2: Snare + HiHat
    s += note_xml("G", 5, 2, "eighth", "P1-I42", "cross")
    s += note_xml("C", 5, 2, "eighth", "P1-I38", None, is_chord=True)
    # 2&: Kick + HiHat (Yellow syncopation!)
    s += note_xml("G", 5, 2, "eighth", "P1-I42", "cross")
    s += note_xml("F", 4, 2, "eighth", "P1-I36", None, is_chord=True, stem="down")
    # 3: Kick + HiHat
    s += note_xml("G", 5, 2, "eighth", "P1-I42", "cross")
    s += note_xml("F", 4, 2, "eighth", "P1-I36", None, is_chord=True, stem="down")
    # 3&: HiHat
    s += note_xml("G", 5, 2, "eighth", "P1-I42", "cross")
    # 4: Snare + HiHat
    s += note_xml("G", 5, 2, "eighth", "P1-I42", "cross")
    s += note_xml("C", 5, 2, "eighth", "P1-I38", None, is_chord=True)
    # 4&: HiHat
    s += note_xml("G", 5, 2, "eighth", "P1-I42", "cross")
    return s

def coldplay_chorus_start():
    s = ""
    # Beat 1: Crash + Kick
    s += note_xml("A", 5, 2, "eighth", "P1-I49", "cross")
    s += note_xml("F", 4, 2, "eighth", "P1-I36", None, is_chord=True, stem="down")
    # 1&: Open HiHat
    s += note_xml("G", 5, 2, "eighth", "P1-I46", "circle-x")
    # 2: Snare + Open HiHat
    s += note_xml("G", 5, 2, "eighth", "P1-I46", "circle-x")
    s += note_xml("C", 5, 2, "eighth", "P1-I38", None, is_chord=True)
    # 2&: Kick + Open HiHat
    s += note_xml("G", 5, 2, "eighth", "P1-I46", "circle-x")
    s += note_xml("F", 4, 2, "eighth", "P1-I36", None, is_chord=True, stem="down")
    # 3: Kick + Open HiHat
    s += note_xml("G", 5, 2, "eighth", "P1-I46", "circle-x")
    s += note_xml("F", 4, 2, "eighth", "P1-I36", None, is_chord=True, stem="down")
    # 3&: Kick + Open HiHat
    s += note_xml("G", 5, 2, "eighth", "P1-I46", "circle-x")
    s += note_xml("F", 4, 2, "eighth", "P1-I36", None, is_chord=True, stem="down")
    # 4: Snare + Open HiHat
    s += note_xml("G", 5, 2, "eighth", "P1-I46", "circle-x")
    s += note_xml("C", 5, 2, "eighth", "P1-I38", None, is_chord=True)
    # 4&: Open HiHat
    s += note_xml("G", 5, 2, "eighth", "P1-I46", "circle-x")
    return s

def coldplay_chorus():
    s = ""
    # Beat 1: Ride/HiHat + Kick
    s += note_xml("G", 5, 2, "eighth", "P1-I46", "circle-x")
    s += note_xml("F", 4, 2, "eighth", "P1-I36", None, is_chord=True, stem="down")
    s += note_xml("G", 5, 2, "eighth", "P1-I46", "circle-x")
    # Beat 2: Snare
    s += note_xml("G", 5, 2, "eighth", "P1-I46", "circle-x")
    s += note_xml("C", 5, 2, "eighth", "P1-I38", None, is_chord=True)
    # Beat 2&: Kick
    s += note_xml("G", 5, 2, "eighth", "P1-I46", "circle-x")
    s += note_xml("F", 4, 2, "eighth", "P1-I36", None, is_chord=True, stem="down")
    # Beat 3: Kick
    s += note_xml("G", 5, 2, "eighth", "P1-I46", "circle-x")
    s += note_xml("F", 4, 2, "eighth", "P1-I36", None, is_chord=True, stem="down")
    s += note_xml("G", 5, 2, "eighth", "P1-I46", "circle-x")
    # Beat 4: Snare
    s += note_xml("G", 5, 2, "eighth", "P1-I46", "circle-x")
    s += note_xml("C", 5, 2, "eighth", "P1-I38", None, is_chord=True)
    s += note_xml("G", 5, 2, "eighth", "P1-I46", "circle-x")
    return s

def coldplay_fill():
    s = ""
    # 1: Kick + HiHat
    s += note_xml("G", 5, 2, "eighth", "P1-I42", "cross")
    s += note_xml("F", 4, 2, "eighth", "P1-I36", None, is_chord=True, stem="down")
    s += note_xml("G", 5, 2, "eighth", "P1-I42", "cross")
    # 2: Snare
    s += note_xml("G", 5, 2, "eighth", "P1-I42", "cross")
    s += note_xml("C", 5, 2, "eighth", "P1-I38", None, is_chord=True)
    s += note_xml("G", 5, 2, "eighth", "P1-I42", "cross")
    # Fill: 16th notes: Snare, Snare, High Tom, Floor Tom
    s += note_xml("C", 5, 1, "16th", "P1-I38", None)
    s += note_xml("C", 5, 1, "16th", "P1-I38", None)
    s += note_xml("E", 5, 1, "16th", "P1-I50", None)
    s += note_xml("E", 5, 1, "16th", "P1-I50", None)
    s += note_xml("A", 4, 2, "eighth", "P1-I43", None)
    s += note_xml("F", 4, 2, "eighth", "P1-I36", None, is_chord=True, stem="down")
    return s

make_musicxml("coldplay_yellow.musicxml", "Coldplay - Yellow (PichuDrummer Style)", 87, [
    coldplay_verse(),
    coldplay_verse(),
    coldplay_verse(),
    coldplay_chorus_start(),
    coldplay_chorus(),
    coldplay_chorus(),
    coldplay_fill(),
    coldplay_verse()
])

# 2. Michael Jackson - Billie Jean (117 BPM)
def billie_jean_bar():
    s = ""
    # 1: Kick + HiHat
    s += note_xml("G", 5, 2, "eighth", "P1-I42", "cross")
    s += note_xml("F", 4, 2, "eighth", "P1-I36", None, is_chord=True, stem="down")
    # 1&: HiHat
    s += note_xml("G", 5, 2, "eighth", "P1-I42", "cross")
    # 2: Snare + HiHat
    s += note_xml("G", 5, 2, "eighth", "P1-I42", "cross")
    s += note_xml("C", 5, 2, "eighth", "P1-I38", None, is_chord=True)
    # 2&: HiHat
    s += note_xml("G", 5, 2, "eighth", "P1-I42", "cross")
    # 3: Kick + HiHat
    s += note_xml("G", 5, 2, "eighth", "P1-I42", "cross")
    s += note_xml("F", 4, 2, "eighth", "P1-I36", None, is_chord=True, stem="down")
    # 3&: HiHat
    s += note_xml("G", 5, 2, "eighth", "P1-I42", "cross")
    # 4: Snare + HiHat
    s += note_xml("G", 5, 2, "eighth", "P1-I42", "cross")
    s += note_xml("C", 5, 2, "eighth", "P1-I38", None, is_chord=True)
    # 4&: HiHat
    s += note_xml("G", 5, 2, "eighth", "P1-I42", "cross")
    return s

make_musicxml("michael_jackson_billie_jean.musicxml", "Michael Jackson - Billie Jean", 117, [
    billie_jean_bar(),
    billie_jean_bar(),
    billie_jean_bar(),
    billie_jean_bar()
])

# 3. AC/DC - Highway to Hell (116 BPM)
def acdc_bar():
    s = ""
    # 1: Crash + Kick
    s += note_xml("A", 5, 2, "eighth", "P1-I49", "cross")
    s += note_xml("F", 4, 2, "eighth", "P1-I36", None, is_chord=True, stem="down")
    # 1&: HiHat
    s += note_xml("G", 5, 2, "eighth", "P1-I42", "cross")
    # 2: Snare + HiHat
    s += note_xml("G", 5, 2, "eighth", "P1-I42", "cross")
    s += note_xml("C", 5, 2, "eighth", "P1-I38", None, is_chord=True)
    # 2&: HiHat
    s += note_xml("G", 5, 2, "eighth", "P1-I42", "cross")
    # 3: Kick + HiHat
    s += note_xml("G", 5, 2, "eighth", "P1-I42", "cross")
    s += note_xml("F", 4, 2, "eighth", "P1-I36", None, is_chord=True, stem="down")
    # 3&: Kick + HiHat
    s += note_xml("G", 5, 2, "eighth", "P1-I42", "cross")
    s += note_xml("F", 4, 2, "eighth", "P1-I36", None, is_chord=True, stem="down")
    # 4: Snare + HiHat
    s += note_xml("G", 5, 2, "eighth", "P1-I42", "cross")
    s += note_xml("C", 5, 2, "eighth", "P1-I38", None, is_chord=True)
    # 4&: HiHat
    s += note_xml("G", 5, 2, "eighth", "P1-I42", "cross")
    return s

make_musicxml("acdc_highway_to_hell.musicxml", "AC/DC - Highway to Hell", 116, [
    acdc_bar(),
    billie_jean_bar(),
    acdc_bar(),
    billie_jean_bar()
])

print("All iconic songs generated successfully!")
