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


class PorterStemmer:

    def __init__(self) -> None:
        """The main part of the stemming algorithm starts here.

        Note that only lower case sequences are stemmed. Forcing to lower case
        should be done before stem(...) is called.
        """

        self.b: str = ""     # buffer for word to be stemmed
        self.k: int = 0
        self.j: int = 0      # j is a general offset into the string

    @staticmethod
    def is_consonant(char: str, i: int, word: str) -> bool:
        """is_consonant(char, i, word) is True <=> char is a consonant."""
        if char in {'a', 'e', 'i', 'o', 'u'}:
            return False
        if char == 'y':
            if i == 0:
                return True
            return not PorterStemmer.is_consonant(word[i - 1], i - 1, word)
        return True

    @staticmethod
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
        while (i <= end) and PorterStemmer.is_consonant(word[i], i, word):
            i += 1
        n = 0
        while True:
            while (i <= end) and not PorterStemmer.is_consonant(word[i], i, word):
                i += 1

            if i > end:
                return n
            n += 1

            while (i <= end) and PorterStemmer.is_consonant(word[i], i, word):
                i += 1

    def vowelinstem(self) -> int:
        """vowelinstem() is TRUE <=> 0,...j contains a vowel"""
        for i in range(self.j + 1):
            if not self.is_consonant(self.b[i], i, self.b):
                return 1
        return 0

    @staticmethod
    def double_consonant(word: str, end: int) -> bool:
        """True <=> word[end-1:end+1] contains a double consonant."""
        if end < 1:
            return False
        if word[end] != word[end - 1]:
            return False
        return PorterStemmer.is_consonant(word[end], end, word)

    def cvc(self, i: int) -> int:
        """cvc(i) is TRUE <=> i-2,i-1,i has the form
             consonant - vowel - consonant
        and also if the second c is not w,x or y. this is used when trying to
        restore an e at the end of a short  e.g.

           cav(e), lov(e), hop(e), crim(e), but
           snow, box, tray.
        """
        if (i < 2
            or not self.is_consonant(self.b[i], i, self.b)
            or self.is_consonant(self.b[i-1], i-1, self.b)
            or not self.is_consonant(self.b[i-2], i-2, self.b)
        ):
            return 0
        ch = self.b[i]
        if ch in ('w', 'x', 'y'):
            return 0
        return 1

    def ends(self, s: str) -> int:
        """ends(s) is TRUE <=> 0,...k ends with the string s."""
        length = len(s)
        if s[length - 1] != self.b[self.k]:  # tiny speed-up
            return 0
        if length > (self.k + 1):
            return 0
        if self.b[self.k - length + 1:self.k + 1] != s:
            return 0
        self.j = self.k - length
        return 1

    def setto(self, s: str) -> None:
        """setto(s) sets (j+1),...k to the characters in the string s,
        readjusting k."""
        length = len(s)
        self.b = self.b[:self.j + 1] + s + self.b[self.j + length + 1:]
        self.k = self.j + length

    def r(self, s: str) -> None:
        """r(s) is used further down."""
        if self.measure_consonant_sequences(self.b, self.j) > 0:
            self.setto(s)

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
        if self.b[self.k] == 's':
            if self.ends("sses"):
                self.k -= 2
            elif self.ends("ies"):
                self.setto("i")
            elif self.b[self.k - 1] != 's':
                self.k -= 1
        if self.ends("eed"):
            if self.measure_consonant_sequences(self.b, self.j) > 0:
                self.k -= 1
        elif (self.ends("ed") or self.ends("ing")) and self.vowelinstem():
            self.k = self.j
            if self.ends("at"):
                self.setto("ate")
            elif self.ends("bl"):
                self.setto("ble")
            elif self.ends("iz"):
                self.setto("ize")
            elif self.double_consonant(self.b, self.k):
                self.k -= 1
                ch = self.b[self.k]
                if ch in ('l', 's', 'z'):
                    self.k += 1
            elif self.measure_consonant_sequences(self.b, self.j) == 1 and self.cvc(self.k):
                self.setto("e")

    def step1c(self) -> None:
        """step1c() turns terminal y to i when there is another vowel in
        the stem."""
        if self.ends("y") and self.vowelinstem():
            self.b = self.b[:self.k] + 'i' + self.b[self.k + 1:]

    def step2(self) -> None:
        """step2() maps double suffices to single ones.
        so -ization ( = -ize plus -ation) maps to -ize etc. note that the
        string before the suffix must give measure_consonant_sequences(self.b, self.j) > 0.
        """
        if self.b[self.k - 1] == 'a':
            if self.ends("ational"):
                self.r("ate")
            elif self.ends("tional"):
                self.r("tion")
        elif self.b[self.k - 1] == 'c':
            if self.ends("enci"):
                self.r("ence")
            elif self.ends("anci"):
                self.r("ance")
        elif self.b[self.k - 1] == 'e':
            if self.ends("izer"):
                self.r("ize")
        elif self.b[self.k - 1] == 'l':
            if self.ends("bli"):
                self.r("ble")  # --DEPARTURE--
            # To match the published algorithm, replace this phrase with
            #   if self.ends("abli"):      self.r("able")
            elif self.ends("alli"):
                self.r("al")
            elif self.ends("entli"):
                self.r("ent")
            elif self.ends("eli"):
                self.r("e")
            elif self.ends("ousli"):
                self.r("ous")
        elif self.b[self.k - 1] == 'o':
            if self.ends("ization"):
                self.r("ize")
            elif self.ends("ation"):
                self.r("ate")
            elif self.ends("ator"):
                self.r("ate")
        elif self.b[self.k - 1] == 's':
            if self.ends("alism"):
                self.r("al")
            elif self.ends("iveness"):
                self.r("ive")
            elif self.ends("fulness"):
                self.r("ful")
            elif self.ends("ousness"):
                self.r("ous")
        elif self.b[self.k - 1] == 't':
            if self.ends("aliti"):
                self.r("al")
            elif self.ends("iviti"):
                self.r("ive")
            elif self.ends("biliti"):
                self.r("ble")
        elif self.b[self.k - 1] == 'g':  # --DEPARTURE--
            if self.ends("logi"):
                self.r("log")
        # To match the published algorithm, delete this phrase

    def step3(self) -> None:
        """step3() dels with -ic-, -full, -ness etc. similar strategy
        to step2."""
        if self.b[self.k] == 'e':
            if self.ends("icate"):
                self.r("ic")
            elif self.ends("ative"):
                self.r("")
            elif self.ends("alize"):
                self.r("al")
        elif self.b[self.k] == 'i':
            if self.ends("iciti"):
                self.r("ic")
        elif self.b[self.k] == 'l':
            if self.ends("ical"):
                self.r("ic")
            elif self.ends("ful"):
                self.r("")
        elif self.b[self.k] == 's':
            if self.ends("ness"):
                self.r("")

    def step4(self) -> None:
        """step4() takes off -ant, -ence etc., in context <c>vcvc<v>."""
        if self.b[self.k - 1] == 'a':
            if self.ends("al"):
                pass
            else:
                return
        elif self.b[self.k - 1] == 'c':
            if self.ends("ance"):
                pass
            elif self.ends("ence"):
                pass
            else:
                return
        elif self.b[self.k - 1] == 'e':
            if self.ends("er"):
                pass
            else:
                return
        elif self.b[self.k - 1] == 'i':
            if self.ends("ic"):
                pass
            else:
                return
        elif self.b[self.k - 1] == 'l':
            if self.ends("able"):
                pass
            elif self.ends("ible"):
                pass
            else:
                return
        elif self.b[self.k - 1] == 'n':
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
        elif self.b[self.k - 1] == 'o':
            if self.ends("ion") and (self.b[self.j] == 's' or
                                     self.b[self.j] == 't'):
                pass
            elif self.ends("ou"):
                pass
            # takes care of -ous
            else:
                return
        elif self.b[self.k - 1] == 's':
            if self.ends("ism"):
                pass
            else:
                return
        elif self.b[self.k - 1] == 't':
            if self.ends("ate"):
                pass
            elif self.ends("iti"):
                pass
            else:
                return
        elif self.b[self.k - 1] == 'u':
            if self.ends("ous"):
                pass
            else:
                return
        elif self.b[self.k - 1] == 'v':
            if self.ends("ive"):
                pass
            else:
                return
        elif self.b[self.k - 1] == 'z':
            if self.ends("ize"):
                pass
            else:
                return
        else:
            return
        if self.measure_consonant_sequences(self.b, self.j) > 1:
            self.k = self.j

    def step5(self) -> None:
        """step5() removes a final -e if measure_consonant_sequences(self.b, self.j) > 1, and changes -ll to -l if
        measure_consonant_sequences(self.b, self.j) > 1.
        """
        self.j = self.k
        if self.b[self.k] == 'e':
            a = self.measure_consonant_sequences(self.b, self.j)
            if a > 1 or (a == 1 and not self.cvc(self.k - 1)):
                self.k -= 1
        if self.b[self.k] == 'l' and self.double_consonant(self.b, self.k) and self.measure_consonant_sequences(self.b, self.j) > 1:
            self.k -= 1

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
        self.b = word
        self.k = len(word) - 1

        self.step1ab()
        self.step1c()
        self.step2()
        self.step3()
        self.step4()
        self.step5()
        return self.b[:self.k + 1]


if __name__ == '__main__':
    stemmer = PorterStemmer()
    stemmer.stem("agreed")
