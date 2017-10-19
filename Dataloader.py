import math
import random
import torch
from torch.autograd import Variable

MAX_WORDPIECE_LEN = 256

class Dataloader(object):
    """Class to Load Language Pairs and Make Batch

    Args:
        path: path to the output of Google SentencePiece

    """   
    def __init__(self, path, batch_size, cuda=False, volatile=False):
        # Need to reload every time because memory error in pickle
        srcFile = open(path + "train.de.id")
        tgtFile = open(path + "train.en.id")
        src = []
        tgt = []
        nb_pairs = 0
        while True:
            src_line = srcFile.readline()
            tgt_line = tgtFile.readline()        
            if src_line=='' and tgt_line=='':
                break            
            src_ids = list(map(int, src_line.strip().split()))
            tgt_ids = list(map(int, tgt_line.strip().split()))
            # skip too short lines
            if len(src_ids)<=1 or len(tgt_ids)<=3:
                continue
            if len(src_ids)<=MAX_WORDPIECE_LEN and len(tgt_ids)<=MAX_WORDPIECE_LEN:
                src.append(src_ids)
                tgt.append(tgt_ids)  
                nb_pairs += 1
        print('%d pairs are converted in the data' %nb_pairs)
        srcFile.close()
        tgtFile.close()
        sorted_idx = sorted(range(nb_pairs), key=lambda i: len(src[i]))
        self.src = [src[i] for i in sorted_idx]
        self.tgt = [tgt[i] for i in sorted_idx]
        self.batch_size = batch_size
        self.nb_pairs = nb_pairs
        self.nb_batches = math.ceil(nb_pairs/batch_size)
        self.cuda = cuda
        self.volatile = volatile
        
    def __len__(self):
        return self.nb_batches  

    def _shuffle_index(self, n, m):
        """Yield indexes for shuffling a length n seq within every m elements"""
        indexes = []
        for i in range(n):
            indexes.append(i)
            if (i+1)%m ==0 or i==n-1:
                random.shuffle(indexes)
                for index in indexes:
                    yield index
                indexes = []
            
    def shuffle(self, m):
        """Shuffle the language pairs within every m elements
        
        This will make sure pairs in the same batch still have similr length.
        """
        shuffled_indexes = self._shuffle_index(self.nb_pairs, m)
        src, tgt = [], []
        for index in shuffled_indexes:
            src.append(self.src[index])
            tgt.append(self.tgt[index])
        self.src = src
        self.tgt = tgt
        
    def _wrap(self, sentences):
        """Pad sentences to same length and wrap into Variable"""
        max_size = max([len(s) for s in sentences])
        out = [s + [0]*(max_size-len(s)) for s in sentences]
        out = torch.LongTensor(out)
        if self.cuda:
            out = out.cuda()
        return Variable(out, volatile=self.volatile)
    
    def __getitem__(self, i): 
        """Generate the i-th batch and wrap in Variable"""
        src_batch = self.src[i*self.batch_size:(i+1)*self.batch_size]
        tgt_batch = self.tgt[i*self.batch_size:(i+1)*self.batch_size]        
        return self._wrap(src_batch), self._wrap(tgt_batch)