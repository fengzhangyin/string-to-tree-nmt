import os
import codecs
import yoav_trees

def main():
    print 'validating trees...'
    base_path = '/home/nlp/aharonr6'
    nematus = base_path + '/git/nematus'
    model_prefix = base_path + '/git/research/nmt/models/de_en_stt_no_bpe_source/de_en_stt_model.npz.npz.best_bleu'
    dev_src = base_path + '/git/research/nmt/data/WMT16/de-en/dev/newstest2015-deen-src.tok.true.de.bpe'
    dev_target = base_path + '/git/research/nmt/models/de_en_stt/newstest2015-deen-src.tok.true.de.bpe.output.trees.dev.best'
    dev_target_sents = base_path + '/git/research/nmt/models/de_en_stt/newstest2015-deen-src.tok.true.de.bpe.output.sents.dev.best'
    alignments_path = base_path + '/git/research/nmt/models/de_en_stt/best_dev_alignments.txt'

    # decode: k - beam size, n - normalize scores by length, p - processes
    decode_command = 'THEANO_FLAGS=mode=FAST_RUN,floatX=float32,device=gpu0,lib.cnmem=0.09,on_unused_input=warn python {}/nematus/translate.py \
     -m {} \
     -i {} \
     -o {} \
     -a {} \
     -k 12 -n -p 5 -v'.format(nematus, model_prefix, dev_src, dev_target, alignments_path)
    os.system(decode_command)

    print 'finished translating {}'.format(dev_src)

    # validate and strip trees
    valid_trees = 0
    total = 0
    with codecs.open(dev_target, encoding='utf-8') as trees:
        with codecs.open(dev_target_sents, 'w', encoding='utf-8') as sents:
           while True:
           	tree = trees.readline()
                if not tree:
                    break  # EOF
                total += 1
                try:
                    parsed = yoav_trees.Tree('Top').from_sexpr(tree)
                    valid_trees += 1
                    sent = ' '.join(parsed.leaves())
                except Exception as e:
                    sent = ' '.join([t for t in tree.split() if '(' not in t and ')' not in t])
                sents.write(sent + '\n')


    # postprocess stripped trees (remove bpe, de-truecase)
    postprocess_command = './postprocess-dev.sh < {} > {}.postprocessed'.format(dev_target_sents, dev_target_sents)
    os.system(postprocess_command)
    print 'postprocessed (de-bped, de-truecase) {} into {}.postprocessed'.format(dev_target_sents, dev_target_sents)
    
    return


if __name__ == '__main__':
    main()
