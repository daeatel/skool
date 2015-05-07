#!/usr/bin/python
# -*- coding: utf-8 -*-
from sumy.nlp.stemmers import Stemmer
from textblob import TextBlob
import collections
import warnings
import re


def wordsCount(text):
    '''Return number of words in the text.

    :param text: text
    :type text: str or unicode
    :returns: Number of words in text
    :rtype: int

    >>> wordsCount('Skákal pes přes oves. Přes zelenou louku')
    7
    '''
    return len(text.split())


def syllablesCount(text):
    '''Return number of "syllables" in text. "Syllable" is a sequence of consonants followed by a sequence of vowels

    :param word: text
    :type word: str or unicode
    :returns: number of syllables in the text
    :rtype: int

    >>> syllablesCount('polokolo')
    4
    >>> syllablesCount('ahoj')
    3
    >>> syllablesCount('konečná')
    3
    >>> syllablesCount('Skákal pes přes oves. Přes zelenou louku')
    17
    '''
    if isinstance(text, str):
        text = unicode(text, 'utf-8')
    text = text.lower()
    ex = r'[^aeiouy]*[aeiouy]*'
    intab = u'áéěíóúůý'
    outtab = u'aeeiouuy'
    intab = [ord(char) for char in intab]
    trantab = dict(zip(intab, outtab))
    morphemes = []
    for word in text.split():
        word = word.translate(trantab)
        while word != '':
            end = re.match(ex, word).end()
            morphemes.append(word[0:end].encode('utf-8'))
            word = word[end:]
    return len(morphemes)


def sentencesCount(text):
    '''Return number of sentences in text

    :param text: text
    :type text: str or unicode
    :returns: Number of sentences
    :rtype: int

    >>> sentencesCount('Skákal pes přes oves. Přes zelenou louku')
    2
    '''
    if isinstance(text, str):
        text = unicode(text, 'utf-8')
    blob = TextBlob(text)
    return len(blob.sentences)

stemmer = Stemmer("czech")


def __stem(text):
    with warnings.catch_warnings():
        warnings.filterwarnings('error')
        try:
            return ' '.join([stemmer(word) for word in text.split()])
        except UserWarning:
            return text


def mistrik(text):
    '''Compute Mistrík's text difficulty index

    :param text: text
    :type text: str or unicode
    :returns: Mistrík's text difficulty index
    :rtype: float

    >>> mistrik('Skákal pes přes oves. Přes zelenou louku')
    44
    >>> mistrik('Když panická ataka vznikne v určité fobické situaci, považuje se v této klasifikaci za projev závažnosti této fobie.')
    14
    '''
    # print text, type(text)
    # print repr(text)
    if isinstance(text, str):
        text = unicode(text, 'utf-8')
    text = __stem(text.lower())
    frequencies = collections.Counter(text.split())
    wordCount = sum(frequencies.values())
    uniqueWordsCount = len(frequencies)
    ls = syllablesCount(text) / wordCount
    lv = wordCount / sentencesCount(text)
    I = wordCount / uniqueWordsCount
    return 50 - ((ls * lv) / I)

if __name__ == '__main__':
    import doctest
    doctest.testmod()
