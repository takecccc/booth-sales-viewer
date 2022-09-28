import pandas as pd
import plotly.express as px
import glob
import sys
import argparse
import datetime as dt

def load_sales_file(filepath):
    usecols=["注文番号", "注文日時", "商品ID", "商品名", "単価", "BOOST", "ユーザー識別コード"]
    df = pd.read_csv(filepath, usecols=usecols, parse_dates=["注文日時"])[usecols]

    # Boothの売り上げ管理CSVは、各種送料や注文日時など、
    # 注文ごとに生じる値の項目は各注文の一行目にのみ表示され、二行目以降は空欄となります。
    df = df.fillna(method="ffill")

    return df

def load_sales_files(files):
    df = pd.concat(map(load_sales_file, files))
    return df

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--files", default="sales_*.csv", help="集計対象のファイル")
    parser.add_argument("--start", help="期間の最初")
    parser.add_argument("--end", help="期間の最後")
    args = parser.parse_args()

    # データの読み込み
    print("load csv")
    files = glob.glob(args.files)

    if len(files) == 0:
        print("no data exists", file=sys.stderr)
        return 1
    df_base = load_sales_files(files)
    df_base = df_base.sort_values("注文日時")

    if args.start is not None:
        df_base = df_base[df_base["注文日時"] >= dt.datetime.strptime(args.start, "%Y/%m/%d")]

    if args.end is not None:
        df_base = df_base[df_base["注文日時"] <= dt.datetime.strptime(args.end, "%Y/%m/%d")]
    
    print(df_base)

    print("analyze data")

    # 月毎の売り上げ
    def show_sales_per_month(df_base):
        df = df_base.groupby(
            [pd.Grouper(key="注文日時", freq="M"), "商品ID", "商品名"]
            ).sum().reset_index()
        df.rename(columns={"単価" : "売り上げ"}, inplace=True)
        fig = px.bar(df, x="注文日時", y="売り上げ", color="商品名", title="月ごとの売り上げ")
        fig.update_xaxes(tick0=df["注文日時"][0], dtick="M1", tickformat="%Y/%m")
        fig.show()

    # 月毎の販売個数
    def show_count_per_month(df_base):
        df = df_base.groupby(
            [pd.Grouper(key="注文日時", freq="M"), "商品ID", "商品名"]
            )[["単価", "BOOST"]].count().reset_index()
        df.rename(columns={"単価" : "販売個数"}, inplace=True)
        fig = px.bar(df, x="注文日時", y="販売個数", color="商品名", title="月ごとの販売個数")
        fig.update_xaxes(tick0=df["注文日時"][0], dtick="M1", tickformat="%Y/%m")
        fig.show()

    # 商品毎の売り上げ
    def show_sales_per_product(df_base):
        df = df_base.groupby(
            ["商品ID", "商品名"]
            )[["単価", "BOOST"]].sum().reset_index()
        df.rename(columns={"単価" : "売り上げ"}, inplace=True)
        fig = px.pie(df, names="商品名", values="売り上げ", title="商品毎の売り上げ")
        fig.show()

    # 商品毎の販売個数
    def show_count_per_product(df_base):
        df = df_base.groupby(
            ["商品ID", "商品名"]
            ).count().reset_index()
        df.rename(columns={"単価" : "販売個数"}, inplace=True)
        fig = px.pie(df, names="商品名", values="販売個数", title="商品毎の販売個数")
        fig.show()

    # 売上推移
    def show_sales_cumsum(df_base):
        t_index = pd.date_range(
                start=df_base["注文日時"].min().date(),
                end=df_base["注文日時"].max().date(),
                freq="M",
                name="注文日時")
        df = df_base.copy()
        df = df.set_index("注文日時").groupby(
            ["商品ID", "商品名"]
            )[["単価", "BOOST"]].apply(
                lambda x: x.resample("M").sum().reindex(t_index, fill_value=0).cumsum()
            ).reset_index()
        df.rename(columns={"単価" : "売り上げ"}, inplace=True)
        print(df)
        fig = px.bar(df, x="注文日時", y="売り上げ", color="商品名", title="累積売上")
        fig.update_xaxes(tick0=df["注文日時"][0], dtick="M1", tickformat="%Y/%m")
        fig.show()
    
    # ユーザー毎の購入額
    def show_purchase_per_user(df_base):
        df = df_base.groupby(
            ["ユーザー識別コード", "商品ID", "商品名"]
        ).sum().reset_index()
        df.rename(columns={"単価" : "購入額"}, inplace=True)
        fig = px.bar(df, x="ユーザー識別コード", y="購入額", color="商品名", title="ユーザー毎の購入額")
        fig.show()
    
    show_sales_per_month(df_base)
    show_count_per_month(df_base)
    show_sales_per_product(df_base)
    show_count_per_product(df_base)
    show_sales_cumsum(df_base)
    show_purchase_per_user(df_base)

    return 0

if __name__ == "__main__":
    sys.exit(main())