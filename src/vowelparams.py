import os
from allosaurus.app import read_recognizer
import audeer
import audformat
import pandas as pd


class VowelParams:
    """Given an audio file, predict VtV and pV like described in the paper
    [*Speech Rhythm Variation in Early-Stage Parkinson's Disease: A Study on Different Speaking Tasks*](https://www.frontiersin.org/journals/psychology/articles/10.3389/fpsyg.2021.668291/full)
    _
    """
    mean_dur = 0.09  # Mean duration of phoneme in seconds
    vowels = ["e", "i", "a", "o", "u", "ɪ", "ɛ", "ɔ", "ʊ", "ʌ", "ɑ", "æ", "uː",
              "y", "ø", "œ", "ɶ", "ɒ", "ɜ", "ɐ", "ɪə", "eə", "ʊə", "aɪ", "aʊ", "ɔɪ", "a:ʊ", "ɔː", "ɪː", "eː", "uː", "oː", "aː", "ɒː", "ɜː", "ɐː", "iː", "eɪ", "oʊ", "aʊə", "aʊəː"]

    def __init__(self, lang="ipa", cache="cache"):
        self.model = read_recognizer()
        self.lang = lang
        self.cache = cache
        self.pause_symbol = "X"  # Symbol for pause in phoneme output
        audeer.mkdir(self.cache)
        pd.options.mode.chained_assignment = None  # default='warn'

    def process(self, audio_path: str) -> tuple:
        """Processes the audio file to extract vowel parameters."""
        phonemes = self.phonemize(audio_path)
        vtv, pv = self.determine_vtv_and_pv(phonemes)
        return (vtv, pv)

    def phonemize(self, audio_path: str) -> pd.DataFrame:
        """Extracts vowel parameters from the audio file."""
        cache_name = f"{audeer.basename_wo_ext(audio_path)}.txt"
        cache_path = audeer.path(self.cache, cache_name)
        if os.path.exists(cache_path):
            print(f"Phoneme file {cache_path} already exists, skipping...")
            phonemes = audformat.utils.read_csv(cache_path)
        else:
            phonemes = self.model.recognize(
                audio_path, self.lang, timestamp=True,)
            phonemes = self.create_phoneme_df(phonemes, audio_path)
            phonemes.to_csv(cache_path, index=False)
        phonemes["cv"] = phonemes["phoneme"].apply(self.get_vowel_consonant)
        return phonemes

    def determine_vtv_and_pv(self, phonemes: pd.DataFrame) -> pd.Series:
        """Compute vtv and pv.

        Given a dataframe with columns dur for duration and cv for C or V, 
        compute two parameters:
        vtv is the accumulated time between two vowels, devided by the number of vowels
        pv is the percenteage of vowel duration in the total duration.

        return two floats
        """

        # remove all rows where cv is not V or C
        phonemes = phonemes[phonemes['cv'].isin(['V', 'C'])]

        if phonemes.empty:
            return 0.0, 0.0

        # if the input dataframe has no duration column named 'dur', creaate it from start and end
        if 'dur' not in phonemes.columns:
            phonemes['dur'] = phonemes['end'] - phonemes['start']

        # Filter for vowels
        vowels_df = phonemes[phonemes['cv'] == 'V']
        if vowels_df.empty:
            return 0.0, 0.0
        # Calculate vtv (time between vowels)
        vtv = 0.0
        #  VtV, the mean interval between two consecutive vowel onset points
        # , disregarding all sequences that are not V or C
        startCount = False
        for i in range(len(phonemes) - 1):
            if startCount:
                vtv += phonemes.iloc[i]['dur']
            if phonemes.iloc[i]['cv'] == 'V':
                vtv += phonemes.iloc[i]['dur']
                startCount = True
        # now count backwards to find the last vowel
        rem_vtv = 0.0
        for i in range(len(phonemes) - 1, -1, -1):
            if phonemes.iloc[i]['cv'] == 'V':
                rem_vtv += phonemes.iloc[i]['dur']
                break
            else:
                rem_vtv += phonemes.iloc[i]['dur']
        vtv -= rem_vtv
        # Average time between vowel onset times
        if len(vowels_df) > 1:
            vtv /= (len(vowels_df) - 1)

        # Calculate pv (percentage of vowel duration)
        total_vowel_duration = vowels_df['dur'].sum()
        total_duration = phonemes['dur'].sum()
        pv = (total_vowel_duration / total_duration) * \
            100 if total_duration > 0 else 0.0

        return vtv, pv

    def get_vowel_consonant(self, phoneme):
        """Determine if a phoneme is a vowel or consonant."""
        if phoneme in self.vowels:
            return 'V'
        elif phoneme == self.pause_symbol:
            return 'X'
        else:
            return 'C'

    def get_results(self):
        """Returns the predicted VtV and pV."""
        return {
            "vowel_duration": self.vowel_duration,
            "vowel_intensity": self.vowel_intensity,
            "vowel_pitch": self.vowel_pitch,
        }

    def create_phoneme_df(self, input: str, wav_name: str) -> pd.DataFrame:
        """Create a DataFrame with phoneme predictions.
        Input something like:

        1.500 0.045 ʂ
        1.560 0.045 e
        1.680 0.045 b

        for each line, make a row with 3rd element as phoneme. first element is start time, and the endtime is the start time of the next row. Finish with an endtime + 45 milliseconds.
        return a DataFrame with columns: phoneme, start, end

        """

        # Parse input lines
        if isinstance(input, str):
            lines = input.strip().splitlines()
        else:
            lines = input

        starts = []
        durations = []
        phonemes = []

        for line in lines:
            parts = line.strip().split()
            if len(parts) != 3:
                continue
            start, dur, ph = parts
            starts.append(float(start))
            durations.append(float(dur))
            phonemes.append(ph)

        data = []
        for i in range(len(starts)):
            start = starts[i]
            ph = phonemes[i]
            if i < len(starts) - 1:
                end = starts[i+1]
            else:
                end = start + mean_dur  # add mean for last phoneme
            dur = end - start
            # If the duration is longer than 3 times the mean duration, set it to mean
            mean_dur = 0.09  # Mean duration in seconds
            if dur > 3 * mean_dur:
                dur = mean_dur
                pause_end = end
                end = start + dur
                # append shortened phoneme
                data.append({'file': wav_name, 'start': start,
                            'end': end, 'dur': dur, 'phoneme': ph})
                start = end  # Update start for next pause
                dur = pause_end - start
                # append pause
                data.append({'file': wav_name, 'start': start,
                            'end': pause_end, 'dur': dur, 'phoneme': self.pause_symbol})
            else:
                data.append({'file': wav_name, 'start': start,
                            'end': end, 'dur': dur, 'phoneme': ph})
            # Round duration to 3 decimal places
            # dur = int((end-start)*1000)/1000.0
        return pd.DataFrame(data, columns=['file', 'start', 'end', 'dur', 'phoneme'])


def main():
    vp = VowelParams()
    audio_path = "test.wav"  # Replace with your audio file path
    # res = vp.process(audio_path)
    phonemes = vp.phonemize(audio_path)
    res = vp.determine_vtv_and_pv(phonemes)

    print(res)


if __name__ == "__main__":
    main()
