"""Porter Stemming Algorithm

This is the Porter stemming algorithm, ported to Python from the
version coded up in ANSI C by the author. It may be be regarded
as canonical, in that it follows the algorithm presented in

Porter, 1980, An algorithm for suffix stripping, Program, Vol. 14,
no. 3, pp 130-137,

only differing from it at the points made --DEPARTURE-- below.

See also https://tartarus.org/martin/PorterStemmer/

The algorithm as described in the paper could be exactly replicated
by adjusting the points of DEPARTURE, but this is barely necessary,
because (a) the points of DEPARTURE are definitely improvements, and
(b) no encoding of the Porter stemmer I have seen is anything like
as exact as this version, even with the points of DEPARTURE!

Release 1: January 2001

:author: Vivake Gupta <v@nano.com>.
:license: Public Domain ("can be used free of charge for any purpose").
"""

__all__ = ("PorterStemmer",)


def is_consonant(word: str, i: int) -> bool:
    """is_consonant(word, i) is True <=> word[i] is a consonant."""
    char = word[i]
    if char in {'a', 'e', 'i', 'o', 'u'}:
        return False
    if char == 'y':
        if word[i] == word[0]:
            return True
        return not is_consonant(word, i - 1)
    return True


def measure_consonant_sequences(word: str, end: int) -> int:
    """Measures the number of consonant sequences in word[:end].
    if c is a consonant sequence and v a vowel sequence, and <..>
    indicates arbitrary presence,

       <c><v>       gives 0
       <c>vc<v>     gives 1
       <c>vcvc<v>   gives 2
       <c>vcvcvc<v> gives 3
       ....
    """
    i = 0
    while (i <= end) and is_consonant(word, i):
        i += 1
    n = 0
    while True:
        while (i <= end) and not is_consonant(word, i):
            i += 1

        if i > end:
            return n
        n += 1

        while (i <= end) and is_consonant(word, i):
            i += 1


def vowel_in_stem(word: str, end: int) -> bool:
    """vowel_in_stem() is True <=> word[:end] contains a vowel"""
    for i in range(end + 1):
        if not is_consonant(word, i):
            return True
    return False


def double_consonant(word: str) -> bool:
    """True <=> word[-2:] contains a double consonant."""
    return (
            len(word) >= 2
            and word[-1] == word[-2]
            and is_consonant(word, -1)
    )


def consonant_vowel_consonant(word: str) -> bool:
    """consonant_vowel_consonant(word) is TRUE <=> word[-3:] has the form
         consonant - vowel - consonant
    and also if the second c is not w,x or y. this is used when trying to
    restore an e at the end of a short  e.g.

       cav(e), lov(e), hop(e), crim(e), but
       snow, box, tray.
    """
    return (
            len(word) >= 3
            and is_consonant(word, -1)
            and not is_consonant(word, -2)
            and is_consonant(word, -3)
            and word[-1] not in {'w', 'x', 'y'}
    )


class PorterStemmer:

    def __init__(self) -> None:
        """The main part of the stemming algorithm starts here.

        Note that only lower case sequences are stemmed. Forcing to lower case
        should be done before stem(...) is called.
        """

        self.word: str = ""  # buffer for word to be stemmed
        self.j: int = 0      # j is a general offset into the string

    def ends(self, string: str) -> bool:
        """True <=> b[:k+1] ends with the given string."""
        if self.word.endswith(string) and string:
            self.j = len(self.word.removesuffix(string)) - 1
            return True
        return False

    def replace(self, ends_with: str, replace: str) -> bool:
        if self.word.endswith(ends_with) and ends_with:
            self.j = len(self.word.removesuffix(ends_with)) - 1
            if measure_consonant_sequences(self.word, self.j) > 0:
                self.word = self.word[:self.j + 1] + replace
            return True
        return False

    def step1ab(self) -> None:
        """step1ab() gets rid of plurals and -ed or -ing. e.g.

           caresses  ->  caress
           ponies    ->  poni
           ties      ->  ti
           caress    ->  caress
           cats      ->  cat

           feed      ->  feed
           agreed    ->  agree
           disabled  ->  disable

           matting   ->  mat
           mating    ->  mate
           meeting   ->  meet
           milling   ->  mill
           messing   ->  mess

           meetings  ->  meet
        """
        if self.word[-1] == 's':
            if self.ends("sses"):
                self.word = self.word[:-2]
            elif self.ends("ies"):
                self.word = self.word[:-3] + 'i'
            elif self.word[-2] != 's':
                self.word = self.word[:-1]
        if self.ends("eed"):
            end = len(self.word) - 1 - 3
            if measure_consonant_sequences(self.word, end) > 0:
                self.word = self.word[:-1]
        elif (self.ends("ed") or self.ends("ing")) and vowel_in_stem(self.word, self.j):
            self.word = self.word[:self.j + 1]
            if self.ends("at"):
                self.word = self.word[:-2] + 'ate'
            elif self.ends("bl"):
                self.word = self.word[:-2] + 'ble'
            elif self.ends("iz"):
                self.word = self.word[:-2] + 'ize'
            elif double_consonant(self.word):
                if self.word[-2] not in {'l', 's', 'z'}:
                    self.word = self.word[:-1]
            elif measure_consonant_sequences(self.word, self.j) == 1 and consonant_vowel_consonant(self.word):
                self.word = self.word[:self.j + 1] + "e"

    def step1c(self) -> None:
        """step1c() turns terminal y to i when there is another vowel in
        the stem."""
        if self.ends("y") and vowel_in_stem(self.word, len(self.word) - 2):
            self.word = self.word[:-1] + 'i'

    def step2(self) -> None:
        """step2() maps double suffices to single ones.
        so -ization ( = -ize plus -ation) maps to -ize etc. note that the
        string before the suffix must give measure_consonant_sequences(self.word, self.j) > 0.
        """
        char = self.word[-2]
        if char == 'a':
            if self.replace("ational", "ate"):
                pass
            elif self.replace("tional", "tion"):
                pass
        elif char == 'c':
            if self.replace("enci", "ence"):
                pass
            elif self.replace("anci", "ance"):
                pass
        elif char == 'e':
            if self.replace("izer", "ize"):
                pass
        elif char == 'l':
            if self.replace("bli", "ble"):  # --DEPARTURE--
                pass
            # To match the published algorithm, replace this phrase with
            #  if self.replace("abli", "able"):
            #      pass
            elif self.replace("alli", "al"):
                pass
            elif self.replace("entli", "ent"):
                pass
            elif self.replace("eli", "e"):
                pass
            elif self.replace("ousli", "ous"):
                pass
        elif char == 'o':
            if self.replace("ization", "ize"):
                pass
            elif self.replace("ation", "ate"):
                pass
            elif self.replace("ator", "ate"):
                pass
        elif char == 's':
            if self.replace("alism", "al"):
                pass
            elif self.replace("iveness", "ive"):
                pass
            elif self.replace("fulness", "ful"):
                pass
            elif self.replace("ousness", "ous"):
                pass
        elif char == 't':
            if self.replace("aliti", "al"):
                pass
            elif self.replace("iviti", "ive"):
                pass
            elif self.replace("biliti", "ble"):
                pass
        # To match the published algorithm, delete this phrase
        elif char == 'g':  # --DEPARTURE--
            if self.replace("logi", "log"):
                pass

    def step3(self) -> None:
        """step3() dels with -ic-, -full, -ness etc. similar strategy
        to step2."""
        char = self.word[-1]
        if char == 'e':
            if self.replace("icate", "ic"):
                pass
            elif self.replace("ative", ""):
                pass
            elif self.replace("alize", "al"):
                pass
        elif char == 'i':
            if self.replace("iciti", "ic"):
                pass
        elif char == 'l':
            if self.replace("ical", "ic"):
                pass
            elif self.replace("ful", ""):
                pass
        elif char == 's':
            if self.replace("ness", ""):
                pass

    def step4(self) -> None:
        """step4() takes off -ant, -ence etc., in context <c>vcvc<v>."""
        char = self.word[-2]
        if char == 'a':
            if self.ends("al"):
                pass
            else:
                return
        elif char == 'c':
            if self.ends("ance"):
                pass
            elif self.ends("ence"):
                pass
            else:
                return
        elif char == 'e':
            if self.ends("er"):
                pass
            else:
                return
        elif char == 'i':
            if self.ends("ic"):
                pass
            else:
                return
        elif char == 'l':
            if self.ends("able"):
                pass
            elif self.ends("ible"):
                pass
            else:
                return
        elif char == 'n':
            if self.ends("ant"):
                pass
            elif self.ends("ement"):
                pass
            elif self.ends("ment"):
                pass
            elif self.ends("ent"):
                pass
            else:
                return
        elif char == 'o':
            if self.ends("ion") and (self.word[self.j] in {'s', 't'}):
                pass
            elif self.ends("ou"):
                pass
            # takes care of -ous
            else:
                return
        elif char == 's':
            if self.ends("ism"):
                pass
            else:
                return
        elif char == 't':
            if self.ends("ate"):
                pass
            elif self.ends("iti"):
                pass
            else:
                return
        elif char == 'u':
            if self.ends("ous"):
                pass
            else:
                return
        elif char == 'v':
            if self.ends("ive"):
                pass
            else:
                return
        elif char == 'z':
            if self.ends("ize"):
                pass
            else:
                return
        else:
            return
        if measure_consonant_sequences(self.word, self.j) > 1:
            self.word = self.word[:self.j + 1]

    def step5(self) -> None:
        """step5() removes a final -e if measure_consonant_sequences(self.word, self.j) > 1, and changes -ll to -l if
        measure_consonant_sequences(self.word, self.j) > 1.
        """
        if self.word[-1] == 'e':
            a = measure_consonant_sequences(self.word, len(self.word) - 1)
            if a > 1 or (a == 1 and not consonant_vowel_consonant(self.word[:-1])):
                self.word = self.word[:-1]
        if self.word[-1] == 'l' and double_consonant(self.word) and measure_consonant_sequences(self.word, len(self.word) - 1) > 1:
            self.word = self.word[:-1]

    def stem(self, word: str) -> str:
        """The string to be stemmed is ``word``.
        The stemmer returns the stemmed string.
        """

        # With this line, strings of length 1 or 2 don't go through the
        # stemming process, although no mention is made of this in the
        # published algorithm. Remove the line to match the published
        # algorithm.
        if len(word) <= 2:
            return word  # --DEPARTURE--

        # copy the parameters into statics
        self.word = word

        self.step1ab()
        self.step1c()
        self.step2()
        self.step3()
        self.step4()
        self.step5()
        return self.word


if __name__ == '__main__':
    stemmer = PorterStemmer()
    stemmer.stem("agreed")
