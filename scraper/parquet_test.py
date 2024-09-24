import pyarrow.parquet as pq
import numpy as np
import pandas as pd
import pyarrow as pa

table = pq.read_table('mariners_game_test.parquet')
resulting_df = table.to_pandas()
print("Parquet rows = {}".format(len(resulting_df)))