import os

import pandas as pd
import unittest
import SSfasta
from IPython.display import display
import warnings
import subprocess

class SSfastaTest(unittest.TestCase):

    def test_length_load(self):
        test_fpath = "cDNAscreen_041020/input/ODB/{0}.fasta".format('ATP5MC1')
        unfiltered_lens = SSfasta.length_srs(test_fpath)
        self.assertTrue(136 in unfiltered_lens.unique())
        self.assertTrue(138 in unfiltered_lens.unique())
        self.assertTrue('9544_0:0008ab' in unfiltered_lens.index)
        self.assertTrue(len(unfiltered_lens) == 29)
        filtered_ids = ['10090_0:0034c4','43179_0:00103c','9606_0:00415a']
        filtered_lens = SSfasta.length_srs(test_fpath,filtered_ids)
        self.assertTrue(136 in filtered_lens.unique())
        self.assertFalse(138 in filtered_lens.unique())
        self.assertFalse('9544_0:0008ab' in filtered_lens.index)
        self.assertTrue(len(filtered_lens) == 3)

class ODBFilterFunctionTest(unittest.TestCase):
    def test_alias_loading(self):
        import SSconfig
        config, spec_list, gene_id_df, tax_table = SSconfig.config_initialization()
        gene_id_df = SSconfig.read_geneID_file("config/cDNAscreen_geneIDs_clean.csv")
        gene_symbols = gene_id_df["gene_symbol"]
        gc_names = []
        for symbol in gene_symbols:
            alias_fpath = "aliases_data/{0}_aliases.txt".format(symbol)
            if not os.path.exists(alias_fpath):
                print(alias_fpath)
                continue
            with open(alias_fpath,'r') as alias_f:
                aliases = [alias.strip() for alias in alias_f.readlines()]
                alias_f.close()
            if len(aliases) == 1:
                print("symbol: {0} has only one alias".format(symbol))
            gc_names.append(aliases[0])
        print(len(gc_names))

        self.assertTrue(len(gene_symbols) == 380)
        #Should be missing one entry for CACB1
        self.assertTrue(len(gc_names) == 379)
        self.assertTrue(sum([symbol in gc_names for symbol in gene_symbols]) == 370)
        mismatch_symbols = [symbol for symbol in gene_symbols if symbol not in gc_names]
        self.assertTrue('ATPIF1' in mismatch_symbols and 'ISPD' in mismatch_symbols)
    
    
    def test_alias_pattern_match(self):
        from ODBfilter import format_odb_field, odb_field_to_re
        import re
        alias_fpath = "aliases_data/ISPD_aliases.txt"
        alias_f = open(alias_fpath,'rt')
        aliases = [alias.strip() for alias in alias_f.readlines()]
        alias_f.close()
        gc_name = aliases[0]
    
        formatted_aliases = [format_odb_field(alias) for alias in aliases]
        alias_res = [odb_field_to_re(alias) for alias in formatted_aliases]
        aliases_pat = "({0})".format("|".join(alias_res))
        test_str_list = ["","CrpPa"," CrPPa   \n","CDP-L-Ribitol Pyrophosphorylase A", "CDP-L-Ribitol Pyrophosphorylase", \
                         "Testicular Tissue Protein Li 97","4-Diphosphocytidyl-2C-Methyl-D-Erythritol Synthase Homolog (Arabidopsis)"]
        test_results = [False,True,True,True,False,True,True]
        for i,test_str in enumerate(test_str_list):
            formatted_test = format_odb_field(test_str)
            result = re.search(aliases_pat, formatted_test) is not None
            try:
                self.assertTrue(result == test_results[i])
            except AssertionError as e:
                print("test str:{0}".format(test_str))
                print("formatted test:{0}".format(formatted_test))
                print("Failed. Result: {0}, Expected result: {1}".format(result, test_results[i]))
                raise e
    
    def test_alias_df_filter(self):
        from ODBfilter import find_alias_matches
        pre_lengths = [31,29,312]
        post_lengths = [31,29,27]
        symbol_list = ["ISPD","ATP5MC1","APEX1"]
        try:
            for i,symbol in enumerate(symbol_list):
                test_tsv = pd.read_csv("cDNAscreen_041020/input/ODB/{0}.tsv".format(symbol),sep='\t',index_col='int_prot_id')

                self.assertTrue(len(test_tsv) == pre_lengths[i])
                am_ids, exact_matches = find_alias_matches(symbol,test_tsv,"tmp/errors.tsv")

                self.assertTrue(len(am_ids) == post_lengths[i])
                print("Passed {0}/{1}".format(i+1,len(symbol_list)))
        except AssertionError:
            print("Failed for symbol: {0}".format(symbol))
            print("Unfiltered length: {0}, Expected length: {1}".format(len(test_tsv,pre_lengths[i])))
            print("alias match length: {0}, Expected length: {1}".format(len(am_ids),post_lengths[i]))


    def test_kalign(self):
        test_inpath = "cDNAscreen_041020/input/ODB/ATP5MC1.fasta"
        test_outpath = "tmp/test_aln.fasta"
        print("Current kalign bin: ")
        subprocess.run(args=['which', 'kalign'])
        print("Testing KALIGN output files. ")
        self.assertTrue(os.path.exists(test_inpath))
        from subprocess import Popen, PIPE
        # full_args = ['kalign','-i',test_inpath,'-o',test_outpath,'-f','fasta'] #deprecated due to PyCharm inconsistencies
        no_args = ['kalign']
        with open(test_inpath,'r') as test_in, open(test_outpath,'wt',encoding='utf-8') as test_out:
            proc = subprocess.run(args=no_args,stdin=test_in,stdout=test_out,text=True)
        self.assertTrue(os.path.exists(test_outpath))
        with open(test_outpath,'r') as test_out_read:
            self.assertTrue(len(test_out_read.readlines()) > 0)


    def test_exact_match_df(self):
        from ODBfilter import exact_match_df
        test_input_path = "cDNAscreen_041020/input/ODB/ATP5MC1.tsv"
        tsv_df = SSfasta.load_tsv_table(test_input_path)
        unfiltered_uniques = tsv_df['pub_gene_id'].unique()
        self.assertTrue('ATP5G1;ATP5MC1' in unfiltered_uniques)
        self.assertTrue('ATP5G1' in unfiltered_uniques)
        self.assertTrue('ATP5MC1' in unfiltered_uniques)
        self.assertTrue('9823_0:003c30' in tsv_df.index and 'LOC100519871' in unfiltered_uniques)
        test_em = ['ATP5G1','ATP5MC1']
        exact_matches = exact_match_df(tsv_df,test_em)
        pgid_uniques = exact_matches['pub_gene_id'].unique()
        self.assertTrue('ATP5G1;ATP5MC1' in pgid_uniques)
        self.assertTrue('ATP5G1' in pgid_uniques)
        self.assertTrue('ATP5MC1' in pgid_uniques)
        self.assertFalse('LOC100519871' in pgid_uniques)

    # @unittest.skip("broken")
    def test_ksr_record_select(self):
        import ODBfilter
        test_symbol_list = ['ATP5MC1','CALM1','ATPIF1','CD151']
        tax_subset = ['10090_0','43179_0','9606_0','10116_0','42254_0','9601_0']
        errors_fpath =  "cDNAscreen_041020/summary/errors.tsv"
        ks_tids = ['10090_0','43179_0','9606_0']
        # errors_fpath = 'tmp/'
        display_match_data = False
        display_ksr = True
        with pd.option_context('display.max_columns',None,'display.max_colwidth',500):
            for symbol in test_symbol_list:
                tsv_inpath = "cDNAscreen_041020/input/ODB/{0}.tsv".format(symbol)
                unfiltered_tsv = SSfasta.load_tsv_table(tsv_inpath,tax_subset=tax_subset)
                unfiltered_fasta = "cDNAscreen_041020/input/ODB/{0}.fasta".format(symbol)
                am_idx,exact_matches = ODBfilter.find_alias_matches(symbol,unfiltered_tsv,errors_fpath)
                am_df = unfiltered_tsv.loc[am_idx]
                em_df = ODBfilter.exact_match_df(unfiltered_tsv,exact_matches)
                if display_match_data:
                    print("alias_match")
                    display(am_df)
                    print("exact_match")
                    display(em_df)
                final_ksr_df = ODBfilter.select_known_species_records(symbol,em_df,am_df,ks_tids,unfiltered_fasta)
                if display_ksr:
                    print("Final known species records: ")
                    display(final_ksr_df)
                if symbol == 'CD151':
                    #Ensure non alias match/ exact match sequences not present in final ksr
                    self.assertFalse(len(final_ksr_df) == len(ks_tids))
                else:
                    self.assertTrue(len(final_ksr_df) == len(ks_tids))

                #Test manual selections cache
                if symbol == 'CALM1':
                    import contextlib
                    import io
                    print("Repeating CALM1 record selection. Should not ask for input (check this yourself)")

                    out_buf = io.StringIO()
                    print("Checking for cached selection output...")
                    with contextlib.redirect_stdout(out_buf):

                        final_ksr_df = ODBfilter.select_known_species_records(symbol, em_df, am_df, ks_tids,
                                                                              unfiltered_fasta)
                        cached_msg = 'To clear selections, either delete corresponding row in file at ' \
                                     'tmp/manual_record_selections.tsv'
                        self.assertIn(cached_msg,out_buf.getvalue())
                    print("Cached selection output found.")

    def test_outgroup_selection(self):
        import ODBfilter
        test_symbol_list = ['ATP5MC1', 'CALM1', 'ATPIF1', 'CD151']
        tax_subset = ['10090_0', '43179_0', '9606_0', '10116_0', '42254_0', '9601_0']
        # symbol = 'ATP5MC1'
        symbol = 'IRF2BP2'
        errors_fpath = 'tmp/outgroup_errors.tsv'
        ks_tids = ['10090_0', '43179_0', '9606_0']
        tsv_inpath = "cDNAscreen_041020/input/ODB/{0}.tsv".format(symbol)
        unfiltered_tsv = SSfasta.load_tsv_table(tsv_inpath, tax_subset=tax_subset)
        unfiltered_fasta = "cDNAscreen_041020/input/ODB/{0}.fasta".format(symbol)
        am_idx, exact_matches = ODBfilter.find_alias_matches(symbol, unfiltered_tsv, errors_fpath)
        am_df = unfiltered_tsv.loc[am_idx]
        em_df = ODBfilter.exact_match_df(unfiltered_tsv, exact_matches)
        final_ksr_df = ODBfilter.select_known_species_records(symbol, em_df, am_df, ks_tids, unfiltered_fasta)

        final_df, dist_srs = ODBfilter.select_outgrup_records(em_df,am_df,ks_tids,final_ksr_df,unfiltered_fasta)
        assert(len(final_df) == len(tax_subset))

class NCBIFilterFunctionTest(unittest.TestCase):

    def test_NCBI_load(self):
        from NCBIfilter import load_NCBI_fasta_df

        test_fpath = "cDNAscreen_041020/input/NCBI/9999/ATP5MC1.fasta"
        taxid_dict = {'Urocitellus parryii':9999}
        ncbi_df = load_NCBI_fasta_df(test_fpath,taxid_dict)
        with pd.option_context('display.max_columns',None):
            self.assertTrue('XP_026242723.1' in ncbi_df.index)
            self.assertTrue('XP_026242723.1' in ncbi_df['NCBI_id'].unique())
            self.assertTrue(9999 in ncbi_df['organism_taxid'].unique())

    def test_select_NCBI_record(self):
        from NCBIfilter import select_NCBI_record
        from ODBfilter import process_input
        import SSconfig
        test_odb_path = "cDNAscreen_041020/input/ODB/ATP5MC1.fasta"
        test_ncbi_path = "cDNAscreen_041020/input/NCBI/9999/ATP5MC1.fasta"

        config, spec_list, gene_id_df, tax_table = SSconfig.config_initialization()
        tax_subset = ['10090_0', '43179_0', '9606_0', '10116_0', '42254_0', '9601_0']
        final_odb = process_input('ATP5MC1',config,tax_subset)
        taxid_dict = {config['NCBITaxName']:config['NCBITaxID']}
        final_combined = select_NCBI_record(test_odb_path,test_ncbi_path,taxid_dict,final_odb,['43179_0'])
        with pd.option_context('display.max_columns', None):
            display(final_combined)


if __name__ == '__main__':
    with warnings.catch_warnings():
        warnings.simplefilter('ignore', category=[ImportWarning,DeprecationWarning])
        unittest.main(buffer=False)