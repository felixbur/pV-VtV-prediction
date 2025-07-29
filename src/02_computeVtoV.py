import pandas as pd
import audformat
from vowelparams import VowelParams
from tqdm import tqdm

lang = "ita"
process_dict = {"phonemes_all.csv": "vtv_pv_predicted.csv",
                "ground_truth.csv": "vtv_pv_truth.csv"}
processor = VowelParams(lang=lang, cache="cache")
for df_name, out_name in process_dict.items():
    df = audformat.utils.read_csv(df_name)
    # make sure df is dataframe
    if isinstance(df, pd.Series):
        df = df.to_frame()
    file_names = df.index.get_level_values(0).unique().values
    # for all filenames, get the dataframe where the multiindex value file is this filename
    data = []
    for file_name in tqdm(file_names, desc=f"Processing files for {df_name}"):
        df_file = df[df.index.get_level_values(0) == file_name]
        # create start and end columns in seconds
        df_file["start"] = df_file.index.get_level_values(1)
        df_file.start = df_file["start"].map(lambda x: x.total_seconds())
        df_file["end"] = df_file.index.get_level_values(2)
        df_file.end = df_file["end"].map(lambda x: x.total_seconds())
        vtv, pv = processor.determine_vtv_and_pv(df_file)
        data.append({'file': file_name, 'vtv': vtv, 'pv': pv})
    df_res = pd.DataFrame(data, columns=['file', 'vtv', 'pv'])
    df_res.to_csv(out_name, index=False)
