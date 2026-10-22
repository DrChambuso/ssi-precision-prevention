import importlib.util
from pathlib import Path
import unittest
import pandas as pd
spec=importlib.util.spec_from_file_location('reconstruction',Path(__file__).resolve().parents[1]/'scripts/reconstruct_surveillance.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
class SourceAggregationTests(unittest.TestCase):
    def data(self):
        return pd.DataFrame({'hospital_procedure_age_id':['X','X','X'],'reporting_year':[2020,2020,2022],'source_file':['h1','h2','full'],'source_row':[1,1,1],'source_record_id':['1','2','3'],'operations':[100,120,80],'ssi_cases':[1,2,0],'predicted_ssi_cases':[0.5,1.5,0]})
    def test_half_years_sum_without_imputing_gap(self):
        d=m.aggregate_rows(self.data());self.assertEqual(d.reporting_year.tolist(),[2020,2022]);self.assertEqual(d.iloc[0].operations,220);self.assertEqual(d.iloc[0].predicted_ssi_cases,2)
    def test_duplicate_source_rejected(self):
        d=self.data();d.loc[1,'source_file']='h1'
        with self.assertRaises(ValueError):m.aggregate_rows(d)
    def test_missing_is_not_zero(self):
        d=self.data();d.loc[0,'ssi_cases']=float('nan')
        with self.assertRaises(ValueError):m.aggregate_rows(d)
if __name__=='__main__':unittest.main()
