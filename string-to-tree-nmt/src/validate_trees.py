import os
import codecs
import yoav_trees

def main():
    print 'validating trees...'
    base_path = '/home/nlp/aharonr6'
    nematus = base_path + '/git/nematus'
    model_prefix = base_path + '/git/research/nmt/models/de_en_stt/de_en_stt_model.npz'
    dev_src = base_path + '/git/research/nmt/data/WMT16/de-en/dev/newstest2015-deen-src.tok.true.de.bpe'
    dev_target = base_path + '/git/research/nmt/models/de_en_stt/newstest2015-deen-src.tok.true.de.bpe.output.trees.dev'
    dev_target_sents = base_path + '/git/research/nmt/models/de_en_stt/newstest2015-deen-src.tok.true.de.bpe.output.sents.dev'
    valid_trees_log = model_prefix + '.valid_trees_log'
    alignments_path = base_path + '/git/research/nmt/models/de_en_stt/dev_alignments.txt'

    # decode: k - beam size, n - normalize scores by length, p - processes
    decode_command = 'THEANO_FLAGS=mode=FAST_RUN,floatX=float32,device=gpu1,lib.cnmem=0.09,on_unused_input=warn python {}/nematus/translate.py \
     -m {}.dev.npz \
     -i {} \
     -o {} \
     -a {} \
     -k 12 -n -p 1 -v'.format(nematus, model_prefix, dev_src, dev_target, alignments_path)
    os.system(decode_command)

    print 'finished translating {}'.format(dev_src)

    # validate and strip trees
    valid_trees = 0
    total = 0
    with codecs.open(dev_target, encoding='utf-8') as trees:
        with codecs.open(dev_target_sents, 'w', encoding='utf-8') as sents:
            with codecs.open(valid_trees_log, 'a', encoding='utf-8') as log:
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
                log.write(str(valid_trees) + '\n')


    # postprocess stripped trees (remove bpe, de-truecase)
    postprocess_command = './postprocess-en.sh < {} > {}.postprocessed'.format(dev_target_sents, dev_target_sents)
    os.system(postprocess_command)
    print 'postprocessed (de-bped, de-truecase) {} into {}.postprocessed'.format(dev_target_sents, dev_target_sents)

    # get current BLEU, compare to last best model, save as best if improved
    bleu_command = './bleu.sh'
    os.system(bleu_command)


if __name__ == '__main__':
    main()
