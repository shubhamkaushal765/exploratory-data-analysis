import pandas as pd
import dataframe_image as dfi


class EDA:
    def __init__(self, path=None, df=None):
        assert any(
            [df, path]
        ), "One of [pandas.DataFrame, filepath: str] must be given. NONE were given."
        assert not all(
            [df, path]
        ), "One of [pandas.DataFrame, filepath: str] must be given. BOTH were given."

        if path is not None:
            df = pd.read_csv(path)
        self.path = path
        self.df = df

    def head(self, index=5):
        print(self.df.head(index))

    def summary(self, drop_cols=["id"], export_png=True):
        df = self.df.copy()
        df = df.drop(columns=drop_cols)

        summry = pd.DataFrame(df.dtypes, columns=["data type"])
        summry["#missing"] = df.isnull().sum().values
        summry["Duplicate"] = df.duplicated().sum()
        summry["#unique"] = df.nunique().values
        desc = pd.DataFrame(df.describe(include="all").transpose())
        summry["min"] = desc["min"].values
        summry["max"] = desc["max"].values
        summry["mean"] = desc["mean"].values
        summry["median"] = desc["50%"]
        summry["std dev"] = desc["std"].values

        if export_png:
            styl_summry = (
                summry.style.set_caption("<b>Summary of the Train Data</b>")
                .background_gradient()
                .set_properties(**{"border": "1.5px dotted", "color": ""})
            )
            print(
                dfi.export(
                    styl_summry, "summary_eda.png", table_conversion="matplotlib"
                )
            )

        return summry
