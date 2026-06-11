#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import fugashi
import ipadic
import re
import jaconv
import unicodedata
import argparse


IpadicFeatures = fugashi.create_feature_wrapper(
    'IpadicFeatures',
    'pos1 pos2 pos3 pos4 cType cForm lemma kana pron'.split(),
)
tagger = fugashi.GenericTagger(ipadic.MECAB_ARGS, wrapper=IpadicFeatures)


def is_kanji(ch):
    return 'CJK UNIFIED IDEOGRAPH' in unicodedata.name(ch)


def is_hiragana(ch):
    return 'HIRAGANA' in unicodedata.name(ch)


def split_okurigana_reverse(text, hiragana):
    """ 
      tested:
        お茶(おちゃ)
        ご無沙汰(ごぶさた)
        お子(こ)さん
    """
    yield (text[0],)
    yield from split_okurigana(text[1:], hiragana[1:])


def split_okurigana(text, hiragana):
    """ 送り仮名 processing
      tested: 
         * 出会(であ)う
         * 明(あか)るい
         * 駆(か)け抜(ぬ)け
    """
    if is_hiragana(text[0]):
        yield from split_okurigana_reverse(text, hiragana)
    if all(is_kanji(_) for _ in text):
        yield text, hiragana
        return
    text = list(text)
    ret = (text[0], [hiragana[0]])
    for hira in hiragana[1:]:
        for char in text:
            if hira == char:
                text.pop(0)
                if ret[0]:
                    if is_kanji(ret[0]):
                        yield ret[0], ''.join(ret[1][:-1])
                        yield (ret[1][-1],)
                    else:
                        yield (ret[0],)
                else:
                    yield (hira,)
                ret = ('', [])
                if text and text[0] == hira:
                    text.pop(0)
                break
            else:
                if is_kanji(char):
                    if ret[1] and hira == ret[1][-1]:
                        text.pop(0)
                        yield ret[0], ''.join(ret[1][:-1])
                        yield char, hira
                        ret = ('', [])
                        text.pop(0)
                    else:
                        ret = (char, ret[1]+[hira])
                else:
                    # char is also hiragana
                    if hira != char:
                        break
                    else:
                        break


def split_furigana(text, debug=False):
    ret = []
    for word in tagger(text):
        origin = word.surface
        if not origin:
            continue

        if debug:
            print(f'[DEBUG] {origin}')
            print(f'[DEBUG]   {word.feature}')

        if any(is_kanji(ch) for ch in origin):
            kana = word.feature.kana
            if kana:
                hiragana = jaconv.kata2hira(kana)

                for pair in split_okurigana(origin, hiragana):
                    ret += [pair]
            else:
                ret += [(origin,)]
        else:
            ret += [(origin,)]

    return ret


def convert(text, format, **kwargs):
    furigana_result = ''

    for pair in split_furigana(text, **kwargs):
        if len(pair) == 2:
            kanji, hira = pair
            if format == 'html':
                furigana_result += f"<ruby><rb>{kanji}</rb><rt>{hira}</rt></ruby>"
            elif format == 'text':
                furigana_result += f"{kanji}({hira})"
        else:
            hira = pair[0]
            furigana_result += hira

    print(furigana_result)
    print()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--html', action='store_true')
    parser.add_argument('-d', '--debug', action='store_true')
    parser.add_argument('input')
    args = parser.parse_args()

    if os.path.isfile(args.input):
        with open(args.input, 'r') as f:
            text = f.read()
    else:
        text = args.input

    for line in text.split('\n'):
        if args.html:
            format = 'html'
        else:
            format = 'text'
        convert(line, format, debug=args.debug)


if __name__ == '__main__':
    main()

