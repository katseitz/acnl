import pandas as pd
import numpy as np
import csv
import os 

directory = '/Users/katharinaseitz/Documents/ACNL/BrainMAPD/N-back processing/data/T2/'
test_file = '/Users/katharinaseitz/Documents/ACNL/BrainMAPD/N-back processing/data/T2/NBack-10081-1.txt'

'''
def sus_out_files(path = dirs[10]):
    #print(path)
    files =  glob.glob(path +'/ses-1/beh/3_MID*.txt')
    #print("here are the files")
    #print(files)
    midshared_files = []
    mid1_files = []
    mid2_files = []
    for file in files: 
        df = file_to_df(file)
        #print(df.head(40))
        #print(('Run1Cue.OnsetTime' in df[0].unique()))
        if('Run1Cue.OnsetTime' in df[0].unique() and 'Run2Cue.OnsetTime' in df[0].unique()):
            midshared_files.append([file, len(df)])
        elif('Run1Cue.OnsetTime' in df[0].unique()):
            mid1_files.append([file, len(df)])
        elif('Run2Cue.OnsetTime' in df[0].unique()):
            mid2_files.append([file, len(df)])
        else:
            print("No sutable MID file for " + path)
            break
        
        #best case 
        if(len(midshared_files) == 1 and len(mid1_files) == 0 and len(mid1_files) == 0): 
            happy_mid(midshared_files[0][0])
        else:
            print("this path has confusing mid files " + path)

'''
def remove_unicode(string):
    """
    Removes unicode characters in string.
    Parameters
    ----------
    string : str
        String from which to remove unicode characters.
    Returns
    -------
    str
        Input string, minus unicode characters.
    """
    return ''.join([val for val in string if 31 < ord(val) < 127])

def file_to_df(text_file, id):
    """
    Convert eprime txt output to a pandas df.
    Parameters
    ----------
    string : str
        Filepath of individual eprime .txt file.
    Returns
    -------
    pandas df
        Input string, minus unicode characters.
    """
    # Load the text file as a list.
    print(text_file)
    with open("data/T2/" + text_file, 'rb') as file:
        text_data = list(file)

    # Call helper to remove unicode.
    filtered_data = [remove_unicode(row.decode('utf-8', 'ignore')) for row in text_data]
    #iterate through the list and append each row
    list_data = []
    for row in filtered_data: 
        if ":" in row: #seperate out variable names and values
            row_as_list = row.split(": ")
            list_data.append(row_as_list)
            
        else:
            list_data.append([row])
    df = pd.DataFrame(list_data) #convert to a df
    df.to_csv('output/T2/' + id + '_raw_T2.csv') #TODO: add session as a variable
    #print(df.head(40)) #uncomment to take a peak
    return df
    
def make_condensed_df(df, id):
    #TODO add header
    #trial type
    block = df.loc[df[0] == 'Running'][1].reset_index() 
    #remove rows from the block df that don't correspond to the block number
    block = block.drop(block[block[1] == 'PracBlockTrials'].index)
    block = block.drop(block[block[1] == 'BlockList'].index)
    block = block.drop(block[block[1].str.contains('TestBlockOrder')].index)
    block = block.drop(block[block[1] == 'NegNeuBlock'].index)
    block = block.drop(block[block[1] == 'NeuNegBlock'].index)
    block = block.drop(block[block[1] == 'CounterBalanceCheck'].index)
    block = block.reset_index() 

    valence = df.loc[df[0] == 'Valence'][1].reset_index()
    #grab acc and RT from when the word is displayed in case pP
    #indicated before they were supposed tp 
    early_acc = df.loc[df[0] == 'TrialWord.ACC'][1].astype(int).reset_index() 
    early_acc = early_acc.replace(2,0) # make 0 incorrect to make the math easier
    early_rt = df.loc[df[0] == 'TrialWord.RT'][1].astype(int).reset_index()
    #acc and RT from blank screen
    acc = df.loc[df[0] == 'TrialBlank.ACC'][1].astype(int).reset_index() #1 is correct is 2 is incorrect
    acc = acc.replace(2,0) # make 0 incorrect to make the math easier
    rt = df.loc[df[0] == 'TrialBlank.RT'][1].astype(int).reset_index()
    #create new df with all of this info
    n_back=pd.concat([block[1],valence[1],rt[1],acc[1], early_rt[1], early_acc[1]],axis=1)
    n_back.columns =['block','valence','reac_time','accuracy', 'early_reac', 'early_acc']
    #print(type(id))
    n_back.to_csv('output/T2/' + id + '_processed_T2.csv') #TODO: add session as a variable
    return n_back


def get_avg_vals(df, id):
    #TODO add header
    #Remove the first two trials as they are guarenteed accurate trials
    df = df.iloc[2:]
     #TODO: fix this logic
    df['reac_time'] = df.apply(lambda df: df['reac_time'] + 500 if df['reac_time'] != 0 else df['reac_time'], axis=1)
    df['final_rt'] = df.apply(lambda df: df['early_reac'] if (df['early_reac'] != 0) else df['reac_time'], axis=1)
    df['final_acc'] = df.apply(lambda df: df['early_acc'] if (df['early_reac'] != 0) else df['accuracy'], axis=1)
    df.to_csv('output/' + id + '_TEST_processed_T2.csv')
    #replace zero reaction times with NaN so that they are not factored into means
    df["final_rt"] = df["final_rt"].replace(0, np.nan)
    df = df.groupby('block', as_index=False).agg({'final_rt':'mean', 'final_acc':'mean'})
    neut_df = df[df["block"].isin(['TestBlock1Trials', 'TestBlock2Trials', 'TestBlock3Trials'])]
    neg_df = df[df["block"].isin(['TestBlock4Trials', 'TestBlock5Trials', 'TestBlock6Trials'])]
    
    df.loc[len(df)] = ['neutral', neut_df['final_rt'].mean(), neut_df['final_acc'].mean()]
    df.loc[len(df)] = ['negative', neg_df['final_rt'].mean(), neg_df['final_acc'].mean()]
    df.to_csv('output/T2/' + id + '_avg_T2.csv') #TODO: add session as a variable
    #for 10081 TODO check if this is true for other P's
    #1, 2, and 3 are neutral
    #4, 5, and 6 are neg
    return [id, neg_df['final_rt'].mean(), neut_df['final_rt'].mean(), 
            neg_df['final_acc'].mean(), neut_df['final_acc'].mean()]


        
def convert_eprime_nback():
    output = []
    output.append(['PID','T2B2Negative.meanRT', 'T2B2Neutral.meanRT', 'T2B2Negative.ACC', 'T2B2Neutral.ACC'])
    for file in os.listdir(directory):
        print(file)
        print("NBack" in file.split("/")[-1])
        if("NBack" in file.split("/")[-1]):
            p_id = file.split("/")[-1].split("-")[1]
            print(p_id)
            df = file_to_df(file, p_id)
            n_back_df = make_condensed_df(df, p_id)
            avg_vals = get_avg_vals(n_back_df, p_id)
            output.append(avg_vals)
            with open('n-back_T2.csv', 'w', newline='') as file:
                writer = csv.writer(file)
                writer.writerows(output)
    
def main():
    convert_eprime_nback()

if __name__ == "__main__":
    main()