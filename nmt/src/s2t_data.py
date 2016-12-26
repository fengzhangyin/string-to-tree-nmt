# -*- coding: utf-8 -*-

"""code for processing corpora for string-to-tree nmt

Usage:
  s2t_data.py [--input INPUT][--trees TREES]

Arguments:

Options:
  -h --help                     show this help message and exit
  --input INPUT                 input file path
  --trees TREES                 trees file path
"""

import codecs
from collections import defaultdict
import os
import yoav_trees
import docopt as do


# TODO:
# write a pipeline that does all:
# tokenize with moses scripts - done
# count words per output sentence - done
# run BPE on both sides -
# extract TSS prefix - done
# write train versions (BPE2BPE): with output length, with output TSS, with both, without anything
# 4 models for 2 language pairs - totals in 8 models, 1 week per model - 8 weeks (one week if takeover)
# can be run in one week on all NLP GPUs / use cyber GPUs?
# start with fr-en TSS, fr-en len
# process is: tokenize -> clean --> truecase --> BPE --> add prefixes --> build dictionaries --> train --> evaluate


MOSES_HOME = '/Users/roeeaharoni/git/mosesdecoder'
BPE_HOME = '/Users/roeeaharoni/git/subword-nmt'
NEMATUS_HOME = '/Users/roeeaharoni/git/nematus'
BPE_OPERATIONS = 89500


def main ():
    # get input file path
    arguments = do.docopt(__doc__)
    if arguments['--input']:
        input_file_path = arguments['--input']
    else:
        print 'no input file specified'
        return

    if arguments['--trees']:
        trees_file_path = arguments['--trees']
    else:
        print 'no trees file specified'
        return

    complete_missing_parse_tress_with_bllip(input_file_path, trees_file_path)

    return

def get_shi_parse_tree_for_tokenized_wmt(sentences_file='../data/shi/Eng_Parse_3/8m.train.trainwords',
                                         trees_file='../data/shi/Eng_Parse_3/8m.train.trainline',
                                         wmt_file= '/Users/roeeaharoni/Google Drive/de-en-wmt16/corpus.parallel.tok.en'):
    text2tree = {}

    # read syntax trees and matching sentences
    with codecs.open(sentences_file, encoding='utf8') as sents:
        with codecs.open(trees_file, encoding='utf8') as trees:
            i = 0
            print 'reading parsed sentences and matching trees...'
            while True:

                i += 1
                sent = sents.readline()
                tree = trees.readline()
                # text2tree[sent.lower().replace(' ','').replace(u'-','').replace(u'–','')] = tree
                text2tree[clean_sent(sent)] = tree
                if 'which has been running for four years , is being continued and extended' in sent:
                    print sent

                if 'When you repeatedly come up against the limits of the domain you are operating in' in sent:
                    print sent

                if 'Gradual Software and callas software today' in sent:
                    print sent

                if 'Puma Flipper Valentines Day Wmns' in sent:
                    print sent

                if 'Keep all partitions and use existing free space' in sent:
                    print sent

                if i%10000==0:
                    print 'read {} trees'.format(i)
                if not sent: break  # EOF
    # return
    i = 0
    found = 0
    with codecs.open(wmt_file, encoding='utf8') as sents:
        with codecs.open(wmt_file + '.parsed', mode='w', encoding='utf8') as output:
            while True:
                i += 1
                if i % 100000 == 0:
                    print '#' * 100
                    print 'looked for {} trees from training corpora, found {} so far'.format(i,found)
                    print '#' * 100
                sent = sents.readline()

                cleaned_sent = clean_sent(sent)

                if cleaned_sent in text2tree:
                    found += 1
                    output.write(text2tree[cleaned_sent])
                else:
                    print u'{} missing tree for: {}\n'.format(i, sent)
                    output.write('MISSING\n')

                if not sent: # EOF
                    print 'looked for {} trees from training corpora, found {} total'.format(i, found)
                    print '(missing {} tress)'.format(i - found)
                    break


def clean_sent(sent):
    return sent.replace('`', '') \
        .replace('...','') \
        .replace(u'…','') \
        .replace(u'„','') \
        .replace(u'´', '') \
        .replace(u'»','') \
        .replace(u'«', '') \
        .replace('{', '') \
        .replace('}', '') \
        .replace('-LCB-','') \
        .replace('-RCB-', '') \
        .replace('_', '') \
        .replace('&quot;', '') \
        .replace('&apos;', '') \
        .replace('@/@', '') \
        .replace('/', '') \
        .replace('-LRB-', '') \
        .replace('-RRB-', '') \
        .replace('-LSB-', '') \
        .replace('-RSB-', '') \
        .replace('(','') \
        .replace(')','') \
        .replace('&#91;','') \
        .replace('&#93;', '') \
        .replace(u'-', '') \
        .replace(u'–', '') \
        .replace(' ','') \
        .lower()



def complete_missing_parse_tress_with_bllip(sentences_file, trees_file):
    # initialize bllip
    from bllipparser import RerankingParser
    rrp = RerankingParser.fetch_and_load('WSJ+Gigaword-v2', verbose=True)

    fixed = 0
    failed = 0

    # read syntax trees and matching sentences
    with codecs.open(sentences_file, encoding='utf8') as sents:
        with codecs.open(trees_file, encoding='utf8') as trees:
            with codecs.open(trees_file + '.fixed', mode='w', encoding='utf8') as trees_output:
                with codecs.open(sentences_file + '.fixed', mode='w', encoding='utf8') as sents_output:
                    i = 0
                    print 'reading parsed sentences and matching trees...'
                    while True:
                        i += 1
                        if i % 100000 == 0:
                            print '*'*100 + 'went through {} lines'.format(i) + '*'*100
                        sent = sents.readline()
                        tree = trees.readline()
                        if 'MISSING' in tree:
                            sents_output.write(sent)
                            try:
                                parsed = rrp.simple_parse(str(sent))
                                trees_output.write(convert_tree(parsed) + '\n')
                                fixed += 1
                            except:
                                trees_output.write('MISSING\n')
                                print 'failed to parse missing tree'
                                failed += 1
                        # else:
                        #     trees_output.write(tree)

                        if not sent: break  # EOF
                    print 'parsed {} missing trees, failed to parse {} missing trees'.format(fixed, failed)
    return


# converts bllip tree (lexicalized, no labels on closing brackets) to xing tree (unlexicalized, labels on closing brac.)
def convert_tree(bllip_tree):
    # example:

    # bllip:
    # '(S1 (S (S (NP (PRP I)) (VP (VBP declare) (VP (VBN resumed) (NP (NP (DT the) (NN session)) (PP (IN of) (NP (DT the) (NNP European) (NNP Parliament))) (VP (VBN adjourned) (PP (IN on) (NP (NNP Friday) (CD 17))) (NP (NNP December) (CD 1999))))))) (, ,) (CC and) (S (NP (PRP I)) (VP (MD would) (VP (VB like) (ADVP (RB once) (RB again)) (S (VP (TO to) (VP (VB wish) (NP (PRP you)) (NP (NP (DT a) (JJ happy) (JJ new) (NN year)) (PP (IN in) (NP (DT the) (NN hope) (SBAR (IN that) (S (NP (PRP you)) (VP (VBD enjoyed) (NP (DT a) (JJ pleasant) (JJ festive) (NN period)))))))))))))) (. .)))'

    # xing shi:
    # '(TOP (S (S (NP PRP )NP (VP VBP (VP VBN (NP (NP DT NN )NP (PP IN (NP DT NNP NNP )NP )PP (VP VBN (PP IN (NP NNP CD )NP )PP (NP NNP CD )NP )VP )NP )VP )VP )S , CC (S (NP PRP )NP (VP MD (VP VB (ADVP RB RB )ADVP (S (VP TO (VP VB (NP PRP )NP (NP (NP DT JJ JJ NN )NP (PP IN (NP DT NN (SBAR IN (S (NP PRP )NP (VP VBD (NP DT JJ JJ NN )NP )VP )S )SBAR )NP )PP )NP )VP )VP )S )VP )VP )S . )S )TOP'

    # remove words and turn into POS terminals:
    root = yoav_trees.Tree.from_sexpr(bllip_tree)
    removed_leaves = remove_leaves(root)
    removed_leaves.label = 'TOP'

    # tokens = str(removed_leaves).split()
    # print 'tree tokens: {}'.format(len(tokens))
    # print tokens
    # print 'sent tokens (tree leaves): {}'.format(len(removed_leaves.leaves()))
    # print [str(l) for l in removed_leaves.leaves()]
    # print removed_leaves.viz()
    return str(removed_leaves)

def remove_leaves(tree):

    non_leaves = []
    for child in tree.children:
        if not child.isleaf():
            non_leaves.append(remove_leaves(child))
    if len(non_leaves) == 0:
        non_leaves = None
    return yoav_trees.Tree(tree.label, non_leaves)



def TODO():
    train_moses_truecase('/Users/roeeaharoni/git/research/nmt/data/WMT16/en-de/train/corpus.parallel.tok.en',
                         '/Users/roeeaharoni/git/research/nmt/models/en-de.en.truecase.model')

    train_moses_truecase('/Users/roeeaharoni/git/research/nmt/data/WMT16/en-de/train/corpus.parallel.tok.de',
                         '/Users/roeeaharoni/git/research/nmt/models/en-de.en.truecase.model')


def bllip_parse(input_file, output_file):
    from bllipparser import RerankingParser
    rrp = RerankingParser.fetch_and_load('WSJ+Gigaword-v2', verbose=True)
    parses = []
    with codecs.open(input_file, encoding='utf8') as sents:
        while True:
            sent = sents.readline()
            print sent
            parse = rrp.simple_parse(str(sent))
            print parse
            print '\n\n'
            parses.append(parse)
            if not sent: break  # EOF
    # acp.bllip_parse('/home/nlp/aharonr6/git/research/nmt/data/WMT16/en-de/dev/newstest2015-deen-ref.en', '/home/nlp/aharonr6/git/research/nmt/data/WMT16/en-de/dev/newstest2015-deen-ref.en')
    return parses



def fr_en_TSS_exp():

    # get file paths
    prefix = '/Users/roeeaharoni/git/research/nmt/data/Eng_Fre_4M/xing'

    train_src = prefix + '.train.txt.tok.fr'
    train_target = prefix + '.train.txt.tok.en'

    dev_src = prefix + '.dev.txt.tok.fr'
    dev_target = prefix + '.dev.txt.tok.en'

    test_src = prefix + '.test.txt.tok.fr'
    test_target = prefix + '.test.txt.tok.en'

    in_lang = 'fr'
    out_lang = 'en'

    all_files = [train_src, train_target, dev_src, dev_target, test_src, test_target]

    src_files = [train_src, dev_src, test_src]

    target_files = [train_target, dev_target, test_target]

    # tokenize
    for file in src_files:
        moses_tokenize(file, file + '.tok', in_lang)

    for file in target_files:
        moses_tokenize(file, file + '.tok', out_lang)

    # clean
    for f in ['train', 'dev', 'test']:
        input_corpus_prefix_path = prefix + '.{}.txt.tok'
        output_corpus_prefix_path = prefix + '.{}.txt.tok.clean'
        moses_clean(input_corpus_prefix_path.format(f), output_corpus_prefix_path.format(f), 'fr', 'en')

    train_src_clean = prefix + '.train.txt.tok.clean.fr'
    train_target_clean = prefix + '.train.txt.tok.clean.en'

    # train src truecase
    src_tc_model_path = prefix + '.train.txt.tok.clean.fr.tcmodel'
    src_tc_model_path = train_moses_truecase(train_src_clean, src_tc_model_path)

    # apply src truecase
    for f in ['train', 'dev', 'test']:
        apply_moses_truecase(prefix + '.{}.txt.tok.clean.fr'.format(f),
                             prefix + '.{}.txt.tok.clean.true.fr'.format(f),
                             src_tc_model_path)

    # train target truecase
    trg_tc_model_path = prefix + '.train.txt.tok.clean.en.tcmodel'
    trg_tc_model_path = train_moses_truecase(train_target_clean, trg_tc_model_path)

    # apply target truecase
    for f in ['train', 'dev', 'test']:
        apply_moses_truecase(
            prefix + '.{}.txt.tok.clean.en'.format(f),
            prefix + '.{}.txt.tok.clean.true.en'.format(f),
            trg_tc_model_path)

    # BPE

    # train bpe
    clean_src_train_file = prefix + '.train.txt.tok.clean.true.en'
    clean_target_train_file = prefix + '.train.txt.tok.clean.true.en'
    bpe_model_path = prefix + '.train.txt.tok.clean.true.fr_en.bpe'
    bpe_model_path = train_BPE(clean_src_train_file, clean_target_train_file, BPE_OPERATIONS, bpe_model_path)

    # apply bpe
    for l in ['fr', 'en']:
        for f in ['train', 'dev', 'test']:
            apply_BPE(
                prefix + '.{}.txt.tok.clean.true.{}'.format(f, l),
                prefix + '.{}.txt.tok.clean.true.bpe.{}'.format(f, l),
                bpe_model_path)

    # add len prefixes
    for f in ['train', 'dev', 'test']:
        src_file = prefix + '.{}.txt.tok.clean.true.bpe.fr'.format(f)
        with codecs.open(src_file, encoding='utf8') as src:
            src_lines = src.readlines()

        output_lengths = get_binned_lengths(
            prefix + '.{}.txt.tok.clean.true.en'.format(f))

        new_src_lines = []
        for i, length in enumerate(output_lengths):
            new_src_lines.append('TL{} '.format(length) + src_lines[i])

        output_file = prefix + '.{}.txt.tok.clean.true.bpe.len.fr'.format(f)
        with codecs.open(output_file, 'w', encoding='utf8') as predictions:
            for i, line in enumerate(new_src_lines):
                predictions.write(u'{}'.format(line))

    # add TSS prefixes
    for f in ['train', 'dev', 'test']:

        src_file = prefix + '.{}.txt.tok.clean.true.bpe.fr'.format(f)

        with codecs.open(src_file, encoding='utf8') as src:
            src_lines = src.readlines()

        output_TSS_prefixes = get_TSS_prefixes(
            prefix + '.{}.txt.tok.clean.true.en'.format(f))

        new_src_lines = []
        for i, length in enumerate(output_lengths):
            new_src_lines.append('TL{} '.format(length) + src_lines[i])

        output_file = prefix + '.{}.txt.tok.clean.true.bpe.len.fr'.format(
            f)
        with codecs.open(output_file, 'w', encoding='utf8') as predictions:
            for i, line in enumerate(new_src_lines):
                predictions.write(u'{}'.format(line))

    # build dictionaries

    # train

    # evaluate


def en_he_len_exp():
    src_file = '/Users/roeeaharoni/git/research/nmt/en-he/IWSLT14.TED.dev2010.he-en.en.tok'
    target_file = '/Users/roeeaharoni/git/research/nmt/en-he/IWSLT14.TED.dev2010.he-en.he.tok'
    output_file = '/Users/roeeaharoni/git/research/nmt/en-he/IWSLT14.TED.dev2010.he-en.en.tok.len'
    add_length_prefix(src_file, target_file, output_file)
    return src_file, target_file


def moses_tokenize(input_file_path, output_file_path, lang):
    commandString = '{}/scripts/tokenizer/tokenizer.perl -l {} < {} > {}'.format(MOSES_HOME,
                                                                                 lang,
                                                                                 input_file_path,
                                                                                 output_file_path)
    os.system(commandString)
    return output_file_path


def moses_clean(input_corpus_prefix_path, output_corpus_prefix_path, src_lang, trg_lang):
    command_string = '{}/scripts/training/clean-corpus-n.perl {} {} {} {} 1 80'.format(
        MOSES_HOME,
        input_corpus_prefix_path,
        src_lang,
        trg_lang,
        output_corpus_prefix_path)
    os.system(command_string)


# input is cleaned files
def train_moses_truecase(src_file_path, tc_model_path):
    # train on clean src
    command_string = '{}/scripts/recaser/train-truecaser.perl -corpus {} -model {}'.format(MOSES_HOME,
                                                                                           src_file_path,
                                                                                           tc_model_path)
    os.system(command_string)
    return tc_model_path


def apply_moses_truecase(input_file_path, output_file_path, tc_model_path):

    # apply on clean source
    command_string = '{}/scripts/recaser/truecase.perl -model {} < {} > {}'.format(MOSES_HOME,
                                                                                   tc_model_path,
                                                                                   input_file_path,
                                                                                   output_file_path)
    os.system(command_string)
    return output_file_path

def train_BPE(src_file_path, trg_file_path, bpe_ops, bpe_model_path):

    # apply on clean source
    command_string = 'cat {} {} | {}/learn_bpe.py -s {} > {}'.format(src_file_path,
                                                                     trg_file_path,
                                                                     BPE_HOME,
                                                                     bpe_ops,
                                                                     bpe_model_path)
    os.system(command_string)
    return bpe_model_path


def apply_BPE(input_file_path, output_file_path, bpe_model_path):
    command_string = '{}/apply_bpe.py -c {} < {} > {}'.format(BPE_HOME,
                                                              bpe_model_path,
                                                              input_file_path,
                                                              output_file_path)
    os.system(command_string)
    return output_file_path


def build_nematus_dictionary(train_src_bpe_file_path, train_target_bpe_file_path):

    # build network dictionary
    command_string = '{}/data/build_dictionary.py {} {}'.format(NEMATUS_HOME,
                                                                train_src_bpe_file_path,
                                                                train_target_bpe_file_path)
    os.system(command_string)


def get_TSS_from_tree(tree):

    tokens = tree.split()
    depth = 0
    depth2labels = {}
    for token in tokens:
        if depth not in depth2labels:
            depth2labels[depth] = []

        if '(' in token:
            depth2labels[depth].append(token.replace('(',''))
            depth += 1

        if ')' in token:
            depth -=1

    return depth2labels[2]



def get_TSS_prefixes(src_file, target_file, trees_file, sentences_file, output_file):

    # Top-level Syntactic Sequence:

    #####NP#### #################VP##################

    # POS tags:

    #  DT   NN  VBZ NN  IN  DT   NNP     NNP    NNP

    # sentence:

    # This site is part of The Imaging Source Network .

    # constituency tree:

    # TOP (S (NP DT NN )NP (VP VBZ (NP (NP NN )NP (PP IN (NP DT NNP NNP NNP )NP )PP )NP )VP . )S )TOP

    # to visualize: (S (NP DT NN ) (VP VBZ (NP (NP NN ) (PP IN (NP DT NNP NNP NNP ) ) ) ) . )

    # should return:

    # ['NP', 'VP']

    new_src_lines = []
    text2tree = {}

    # read syntax trees and matching sentences
    with codecs.open(sentences_file, encoding='utf8') as sents:
        with codecs.open(trees_file, encoding='utf8') as trees:
            i = 0
            print 'reading parsed sentences and matching trees...'
            while True and i < 1000:
                i += 1
                sent = sents.readline()
                tree = trees.readline()
                text2tree[sent] = tree
                if not sent: break  # EOF
                # sent_lines = sent.readlines()
                # sent_lines = [next(sent) for x in xrange(600000)]
            # tree_lines = trees.readlines()
            # tree_lines = [next(trees) for x in xrange(600000)]
            # for i, treeline in enumerate(tree_lines):
            #     text2tree[sent_lines[i]] = treeline

    TSS_strings = []
    TSS_with_lex_trees = []
    TSS_with_clean_trees = []
    text2lextree = {}
    for text in text2tree:

        # get the raw tree
        TSS = get_TSS_from_tree(text2tree[text])

        # clean the tree for visualization
        clean_tree = []
        for s in text2tree[text].split():
            if ')' in s:
                clean_tree.append(')')
            else:
                clean_tree.append(s)

        # clean the tree and add words for visualization
        lex_tree = []
        words = text.split()
        i = 0
        for s in text2tree[text].split():
            if ')' in s:
                lex_tree.append(')')
            else:
                if '(' in s:
                    lex_tree.append(s)
                else:
                    # pos, replace with word
                    lex_tree.append('(' + s)
                    lex_tree.append(words[i])
                    lex_tree.append(')')
                    i += 1

        text2lextree[text] = ' '.join(lex_tree)

        TSS_with_lex_trees.append(' '.join(TSS) + '_____' + ' '.join(lex_tree))
        TSS_strings.append(' '.join(TSS))
        TSS_with_clean_trees.append(' '.join(clean_tree))

    from collections import Counter

    TSS_counter = Counter(TSS_strings)
    x = TSS_counter.most_common()
    TSS_distinct = list(set(TSS_strings))

    # read parallel data
    with codecs.open(src_file, encoding='utf8') as src:
        with codecs.open(target_file, encoding='utf8') as trgt:
            print 'reading source sentences...'
            # src_lines = src.readlines()
            src_lines = [next(src) for x in xrange(100000)]

            print 'reading target sentences...'
            # trgt_lines = trgt.readlines()
            trgt_lines = [next(trgt) for x in xrange(100000)]

    print 'looking for trees...'
    found = 0
    total = 0
    TSS_strings = []
    for i, line in enumerate(trgt_lines):
        total += 1
        if line in text2tree:
            # found the tree for the sentence
            found += 1
            print text2tree[line], '\n', line, '\n\n'

            tree = text2tree[line]
            TSS = get_TSS_from_tree(tree)
            TSS_strings.append(' '.join(TSS))

    print 'found trees for {} out of {} sentences'.format(found, total)
    return TSS_strings


def add_length_prefix(src_file, target_file, output_file):
    len_histogram = defaultdict(int)
    binned_histogram = defaultdict(int)
    BIN_SIZE = 5
    binned_lens = []
    new_src_lines = []
    with codecs.open(src_file, encoding='utf8') as src:
        with codecs.open(target_file, encoding='utf8') as trgt:
            print 'tokenizing...'
            src_lines = src.readlines()
            trgt_lines = trgt.readlines()
            for i, line in enumerate(trgt_lines):
                tokens = line.split()
                length = len(tokens)
                len_histogram[length] = len_histogram[length] + 1

                # compute bin
                if length % BIN_SIZE == 0:
                    binned_length = length
                else:
                    # if not in bin go to the next bin
                    binned_length = length - length % BIN_SIZE + BIN_SIZE
                binned_histogram[binned_length] += 1
                new_src_lines.append('TL{} '.format(binned_length) + src_lines[i])
                binned_lens.append(binned_length)


    for i in xrange(100):
        print u'{}\n{}'.format(new_src_lines[i], trgt_lines[i])
    with codecs.open(output_file, 'w', encoding='utf8') as predictions:
        for i, line in enumerate(new_src_lines):
            predictions.write(u'{}'.format(line))
    for key in len_histogram:
        print key, '\t', len_histogram[key]
    for key in binned_histogram:
        print key, '\t', binned_histogram[key]


def get_binned_lengths(target_file, bin_size = 5):
    binned_lens = []

    with codecs.open(target_file, encoding='utf8') as trgt:
        trgt_lines = trgt.readlines()
        for i, line in enumerate(trgt_lines):
            tokens = line.split()
            length = len(tokens)

            # compute bin
            if length % bin_size == 0:
                binned_length = length
            else:
                # if not in bin go to the next bin
                binned_length = length - length % bin_size + bin_size
            binned_lens.append(binned_length)

    for i in xrange(10):
        print 'sanity check:'
        print 'len is {} for: {}'.format(binned_lens[i], trgt_lines[i])
    return binned_lens




if __name__ == '__main__':
    main()