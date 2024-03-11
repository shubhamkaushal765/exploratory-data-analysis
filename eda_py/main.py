from _eda_object import EDA

if __name__ == '__main__':
    path = "../data/train.csv"
    eda_df = EDA(path=path)
    summary = eda_df.summary()
    