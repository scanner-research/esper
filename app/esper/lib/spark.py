from pyspark.sql import SparkSession, Row
import csv
import os
import psutil
from multiprocessing import cpu_count
from iterextras import par_for
import subprocess as sp

SPARK_DATA_PREFIX = '/app/data/spark'
total_mem = psutil.virtual_memory().total // (1024**3)
SPARK_MEMORY = '{}g'.format(int(total_mem * 0.9))


class TableDelegator:
    def __init__(self, spark):
        self._spark = spark

    def __getattr__(self, k):
        return self._spark.load(k)


class SparkWrapper:
    def __init__(self):
        self.spark = SparkSession.builder \
            .master("spark://spark:7077") \
            .config("spark.driver.memory", SPARK_MEMORY) \
            .config("spark.worker.memory", SPARK_MEMORY) \
            .config("spark.executor.memory", SPARK_MEMORY) \
            .config("spark.driver.maxResultSize", SPARK_MEMORY) \
            .config("spark.rpc.message.maxSize", "2047") \
            .config('spark.driver.allowMultipleContexts', 'true') \
            .getOrCreate()
        self.sc = self.spark.sparkContext
        self.table = TableDelegator(self)

    # queryset to dataframe
    def qs_to_df(self, qs):
        qs.save_to_csv('tmp')
        return self.load_csv('/app/data/postgres/tmp.csv')

    def load_csv(self, path):
        return self.spark.read.format("csv").option("header", "true").option(
            "inferSchema", "true").load(path)

    def bulk_import_csv(self, models, paths, workers=8):
        model_names = [m._meta.db_table for m in models]

        def load(arg):
            (model_name, path) = arg
            spark_path = '/app/data/spark/{}'.format(model_name)
            if os.path.isdir(spark_path):
                sp.check_call('rm -r {}'.format(spark_path), shell=True)
            df = self.load_csv(path)
            self.save(model_name, df)

        par_for(load, list(zip(model_names, paths)), workers=workers)

    # dictionaries to dataframe
    def dicts_to_df(self, ds):
        return self.spark.createDataFrame(
            self.sc.parallelize(ds, cpu_count()).map(lambda d: Row(**d)))

    # array of tuples to dataframe, with column names in cols
    def arraytups_to_df(self, array, cols):
        self.spark.createDataFrame(array, cols)

    def append_column(self, df, name, col):
        csv_path = '/app/{}.csv'.format(name)
        with open(csv_path, 'wb') as f:
            writer = csv.writer(f, delimiter=',')
            writer.writerow(['id', name])
            for id, x in col:
                writer.writerow([id, str(x).lower() if x is not None else ''])
        col_df = self.spark.read.format("csv").option("header", "true").option(
            "inferSchema", "true").load(csv_path)
        # os.remove(csv_path)

        # wcrichto 1-26-18: withColumn appears to fail in practice with inscrutable errors, so
        # we have to use a join instead.
        return df.join(col_df, df.id == col_df.id).drop(col_df.id)

    def median(self, df, col):
        return df.approxQuantile(col, [0.5], 0.001)[0]

    def load(self, key):
        if not isinstance(key, str):
            key = key._meta.db_table
        key = '{}/{}'.format(SPARK_DATA_PREFIX, key)
        return self.spark.read.load(key)

    def save(self, key, df):
        key = '{}/{}'.format(SPARK_DATA_PREFIX, key)
        df.write.save(key)


spark = SparkWrapper()
