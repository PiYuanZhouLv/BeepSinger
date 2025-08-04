
BASE_FREQUENCY = {
    '1': 440*(2**(3/12)),
    '2': 440*(2**(5/12)),
    '3': 440*(2**(7/12)),
    '4': 440*(2**(8/12)),
    '5': 440*(2**(10/12)),
    '6': 440*(2**(12/12)),
    '7': 440*(2**(14/12)),
    '0': 0
}
WHITESPACE = 0.02

def convert(song, mode="PT"):
    assert mode in ('PL', 'PT')
    nab, rythme = song.split(';')
    name, bpm = nab.split('@')
    beat = 60 / int(bpm)
    notes = []
    chars = list(rythme)

    stage = 'pre' # Or 'bhd'
    frequency = 1
    last = beat
    hold_on = False
    while chars:
        char = chars.pop(0)
        if stage == 'pre':
            match char:
                case '#':
                    frequency *= 2 ** (1/12)
                case 'b':
                    frequency /= 2 ** (1/12)
                case '1'|'2'|'3'|'4'|'5'|'6'|'7'|'0':
                    frequency *= BASE_FREQUENCY[char]
                    stage = 'bhd'
        else:
            match char:
                case '^':
                    frequency *= 2
                case 'v':
                    frequency /= 2
                case '.':
                    last *= 1.5
                case '/':
                    last /= 2
                case '-':
                    last += beat
                case '_':
                    hold_on = True
                case 'b'|'#'|'1'|'2'|'3'|'4'|'5'|'6'|'7'|'0':
                    if hold_on or last <= WHITESPACE:
                        if notes and notes[-1][0] == frequency:
                            notes[-1][1] += last
                        else:
                            notes.append([frequency, last])
                    else:
                        if notes and notes[-1][0] == frequency:
                            notes[-1][1] += last - WHITESPACE
                        else:
                            notes.append([frequency, last-WHITESPACE])
                        if frequency == 0:
                            notes[-1][1] += WHITESPACE
                        else:
                            notes.append([0, WHITESPACE])
                    stage = 'pre'
                    frequency = 1
                    last = beat
                    hold_on = False
                    chars.insert(0, char)
    if notes and notes[-1][0] == frequency:
        notes[-1][1] += last
    else:
        notes.append([frequency, last])  # Last note.
    
    formatted = []
    for note in notes:
        f, t = note
        p = round(2000000 / f) - 1 if f else -1
        l = round(t * (2000000 / (p+1))) if f else round(t * 1000)
        formatted.append(p)
        formatted.append(l if mode == 'PL' else round(t*1000))
    formatted += [-1, 0]  # End Marker
    
    return name, formatted

def generate_c_array(var, array):
    return f'const int {var}[] = {{{", ".join(map(str, array))}}};\n'

if __name__ == '__main__':
    # import sys
    # if len(sys.argv) == 1 or '-h' in sys.argv or '--help' in sys.argv:
    #     print('Convertor that change Simplified-Song-Format into Period-Last-Format or Period-Time-Format.')
    #     print('Usage: python convert.py in.txt [out.h] --mode PT/PL')
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument('file_in', metavar='in.txt')
    ap.add_argument('file_out', metavar='out.h', nargs='?')
    ap.add_argument('--mode', choices=['PL', 'PT'], default='PT')
    arg = ap.parse_args()
    if not arg.file_out:
        arg.file_out = arg.file_in[:-4]+'.h'
    with (open(arg.file_in, encoding='utf-8') as fin,
          open(arg.file_out, 'w', encoding='utf-8') as fout):
        fout.write('#ifndef _SONG_H_\n#define _SONG_H_\n\n// Format: '+arg.mode+'\n\n')
        for ln, line in enumerate(fin, 1):
            if '@' in line:
                try:
                    name, formatted = convert(line, arg.mode)
                except:
                    print(f'Error occurred when converting line {ln}.')
                    raise
                else:
                    fout.write(generate_c_array(name, formatted))
                    print(f'Convert song "{name}" (line {ln}) successfully.')
            else:
                print(f'Skip line {ln}.')
        fout.write('\n#endif\n')
        print('Finished convert.')
