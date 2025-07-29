import os
import audeer
import audformat
import pandas as pd
from vowelparams import VowelParams

lang = "ita"
root_dir = "HC_speakers"
gt_file = "ground_truth.csv"
out_dir = "."
cache = "cache"
mean_dur = 0.09  # Mean duration in seconds
vowels = ["e", "i", "a", "o", "u", "ɪ", "ɛ", "ɔ", "ʊ", "ʌ", "ɑ", "æ", "uː",
          "y", "ø", "œ", "ɶ", "ɒ", "ɜ", "ɐ", "ɪə", "eə", "ʊə", "aɪ", "aʊ", "ɔɪ", "a:ʊ", "ɔː", "ɪː", "eː", "uː", "oː", "aː", "ɒː", "ɜː", "ɐː", "iː", "eɪ", "oʊ", "aʊə", "aʊəː"]
pause_symbol = "X"  # Symbol for pause in phoneme output


audeer.mkdir(out_dir)
audeer.mkdir(cache)

# Read in the ground truth file in audformat, with one column named cv
gt_df = audformat.utils.read_csv(gt_file)
wav_files = gt_df.index.get_level_values(0).unique().values
files_num = len(wav_files)

processor = VowelParams(lang=lang, cache=cache)

df_all = pd.DataFrame()
for i in range(files_num):
    wav_file = wav_files[i]
    outfile_name = f"{audeer.basename_wo_ext(wav_file)}.txt"
    outfile_path = audeer.path(cache, outfile_name)
    if os.path.exists(outfile_path):
        print(f"Phoneme file {outfile_path} already exists, skipping")
        phonemes = audformat.utils.read_csv(outfile_path)
    else:
        print(f"Processing {wav_file}...")
        phonemes = processor.phonemize(wav_file)
        print(f"Predicted phonemes for {wav_file}: {phonemes}")
        phonemes.to_csv(outfile_path, index=False)
        print(f"Phonemes saved to {outfile_path}\n")
    df_all = pd.concat([df_all, phonemes])
# save the final DataFrame to a CSV file
out_file = audeer.path(out_dir, "phonemes_all.csv")
df_all.to_csv(out_file)
